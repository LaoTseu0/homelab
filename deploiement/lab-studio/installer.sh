#!/usr/bin/env bash
# installer.sh — déploie la configuration de lab-studio depuis le repo.
#
# Idempotent : à relancer après chaque `git pull` qui touche deploiement/,
# ou sur un serveur fraîchement réinstallé.
#
# Prérequis (voir serveurs/lab-studio/installation.md) :
#   Ubuntu Server + drivers NVIDIA + Docker + NVIDIA Container Toolkit
#   + alsa-utils + XVF3800 branché en USB.
#
# Usage :   cd deploiement/lab-studio && bash installer.sh

set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_ROOT="/srv/jarvis"
SECRETS_DIR="$DEPLOY_ROOT/secrets"
GRAFANA_SECRETS_FILE="$SECRETS_DIR/grafana.env"
EXPORTER_SECRETS_FILE="$SECRETS_DIR/jarvis-exporter.env"
DEPLOY_USER="$(id -un)"
DEPLOY_GROUP="$(id -gn)"
COMPOSE_ARGS=(
  --profile jarvis-exporter
  -f "$DEPLOY_ROOT/docker-compose.yml"
  -f "$DEPLOY_ROOT/docker-compose.observability.yml"
)

echo "== Vérification des prérequis =="
command -v docker >/dev/null || { echo "ERREUR : Docker manquant — voir installation.md"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "ERREUR : plugin Docker Compose manquant"; exit 1; }
command -v arecord >/dev/null || { echo "ERREUR : alsa-utils manquant (sudo apt install alsa-utils)"; exit 1; }
docker info 2>/dev/null | grep -qi nvidia || echo "AVERTISSEMENT : runtime NVIDIA non détecté dans Docker (nvidia-ctk runtime configure ?)"

echo "== 1/6 Arborescence /srv =="
sudo mkdir -p \
  "$DEPLOY_ROOT" \
  /srv/homeassistant \
  /srv/wyoming/whisper \
  /srv/wyoming/piper
sudo install -d -m 0700 -o "$DEPLOY_USER" -g "$DEPLOY_GROUP" "$SECRETS_DIR"

echo "== 2/6 Configuration et secrets =="
sudo cp "$DIR/docker-compose.yml" "$DEPLOY_ROOT/docker-compose.yml"
sudo cp \
  "$DIR/docker-compose.observability.yml" \
  "$DEPLOY_ROOT/docker-compose.observability.yml"
sudo mkdir -p "$DEPLOY_ROOT/observability"
sudo cp -R "$DIR/observability/." "$DEPLOY_ROOT/observability/"

if [ ! -f "$GRAFANA_SECRETS_FILE" ]; then
  GRAFANA_PASSWORD="$(od -An -N18 -tx1 /dev/urandom | tr -d ' \n')"
  (
    umask 077
    {
      echo "GF_SECURITY_ADMIN_USER=admin"
      echo "GF_SECURITY_ADMIN_PASSWORD=$GRAFANA_PASSWORD"
    } > "$GRAFANA_SECRETS_FILE"
  )
  echo "Secret Grafana généré dans $GRAFANA_SECRETS_FILE"
else
  echo "Secret Grafana existant conservé : $GRAFANA_SECRETS_FILE"
fi

if [ ! -f "$EXPORTER_SECRETS_FILE" ]; then
  (
    umask 077
    {
      echo "HOME_ASSISTANT_TOKEN="
      echo "HOME_ASSISTANT_PIPELINE_IDS="
    } > "$EXPORTER_SECRETS_FILE"
  )
  echo "Secret exporteur créé dans $EXPORTER_SECRETS_FILE"
  echo "Ajouter HOME_ASSISTANT_TOKEN pour activer les métriques Assist."
else
  echo "Secret exporteur existant conservé : $EXPORTER_SECRETS_FILE"
fi

echo "== 3/6 Conteneurs (deux fichiers Compose combinés) =="
docker volume inspect ollama >/dev/null 2>&1 || docker volume create ollama
docker compose "${COMPOSE_ARGS[@]}" config --quiet
docker compose "${COMPOSE_ARGS[@]}" up -d --build
# Les fichiers provisionnés sont montés en lecture seule : ces redémarrages
# appliquent aussi leurs modifications lors d'un redéploiement idempotent.
docker compose "${COMPOSE_ARGS[@]}" restart prometheus grafana
docker compose "${COMPOSE_ARGS[@]}" up -d --wait --wait-timeout 180

echo "== 4/6 Modèles Ollama =="
# Modèles (no-op rapide s'ils sont déjà présents dans le volume)
docker exec ollama ollama pull qwen3:4b-instruct-2507-q4_K_M
# Embeddings pour le RAG de la doc (formation module 2, ~270 Mo)
docker exec ollama ollama pull nomic-embed-text

echo "== 5/6 wyoming-satellite (sur l'hôte — voir etat.md §2.4) =="
if [ ! -d "$HOME/wyoming-satellite" ]; then
  git clone https://github.com/rhasspy/wyoming-satellite.git "$HOME/wyoming-satellite"
  (cd "$HOME/wyoming-satellite" && script/setup)
fi

echo "== 6/6 Service systemd du satellite =="
sudo cp "$DIR/wyoming-satellite.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now wyoming-satellite
sudo systemctl restart wyoming-satellite   # prend en compte un .service modifié

echo
echo "== Terminé. Vérifications : =="
echo "   docker compose ${COMPOSE_ARGS[*]} ps   # 9 conteneurs"
echo "   systemctl status wyoming-satellite     # active (running)"
echo "   journalctl -u wyoming-satellite -f     # logs du satellite"
echo "   Grafana : http://<IP-de-lab-studio>:3000"
echo "   Identifiants Grafana : $GRAFANA_SECRETS_FILE"
echo "   Jeton Home Assistant : $EXPORTER_SECRETS_FILE"
echo "   Benchmark Ollama manuel :"
echo "   curl -sS -X POST http://127.0.0.1:9102/benchmark/ollama \\"
echo "     -H 'Content-Type: application/json' -d '{\"num_predict\":64}'"
echo "   puis : « héï djarvis, quelle heure est-il ? »"
echo
echo "NB après un reset complet : /srv/homeassistant est vierge → refaire"
echo "l'onboarding HA (ou restaurer un backup). La carte audio est adressée"
echo "par nom (CARD=Array), stable entre boots — si le satellite ne trouve"
echo "pas le micro, vérifier le nom avec : arecord -l"

#!/usr/bin/env bash
# installer.sh — déploie la configuration de jarvis-central depuis le repo.
#
# Idempotent : à relancer après chaque `git pull` qui touche deploiement/,
# ou sur un serveur fraîchement réinstallé.
#
# Prérequis (voir serveurs/jarvis-central/installation.md) :
#   Ubuntu Server + drivers NVIDIA + Docker + NVIDIA Container Toolkit
#   + alsa-utils + XVF3800 branché en USB.
#
# Usage :   cd deploiement/jarvis-central && ./installer.sh

set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "== Vérification des prérequis =="
command -v docker >/dev/null || { echo "ERREUR : Docker manquant — voir installation.md"; exit 1; }
command -v arecord >/dev/null || { echo "ERREUR : alsa-utils manquant (sudo apt install alsa-utils)"; exit 1; }
docker info 2>/dev/null | grep -qi nvidia || echo "AVERTISSEMENT : runtime NVIDIA non détecté dans Docker (nvidia-ctk runtime configure ?)"

echo "== 1/4 Arborescence /srv =="
sudo mkdir -p /srv/jarvis /srv/homeassistant /srv/wyoming/whisper /srv/wyoming/piper

echo "== 2/4 Conteneurs (docker compose) =="
docker volume inspect ollama >/dev/null 2>&1 || docker volume create ollama
sudo cp "$DIR/docker-compose.yml" /srv/jarvis/docker-compose.yml
docker compose -f /srv/jarvis/docker-compose.yml up -d
# Modèle LLM (no-op rapide s'il est déjà présent dans le volume)
docker exec ollama ollama pull qwen3:4b-instruct-2507-q4_K_M

echo "== 3/4 wyoming-satellite (sur l'hôte — voir etat.md §2.4) =="
if [ ! -d "$HOME/wyoming-satellite" ]; then
  git clone https://github.com/rhasspy/wyoming-satellite.git "$HOME/wyoming-satellite"
  (cd "$HOME/wyoming-satellite" && script/setup)
fi

echo "== 4/4 Service systemd du satellite =="
sudo cp "$DIR/wyoming-satellite.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now wyoming-satellite
sudo systemctl restart wyoming-satellite   # prend en compte un .service modifié

echo
echo "== Terminé. Vérifications : =="
echo "   docker ps                              # 5 conteneurs Up"
echo "   systemctl status wyoming-satellite     # active (running)"
echo "   journalctl -u wyoming-satellite -f     # logs du satellite"
echo "   puis : « héï djarvis, quelle heure est-il ? »"
echo
echo "NB après un reset complet : /srv/homeassistant est vierge → refaire"
echo "l'onboarding HA (ou restaurer un backup). La carte audio est adressée"
echo "par nom (CARD=Array), stable entre boots — si le satellite ne trouve"
echo "pas le micro, vérifier le nom avec : arecord -l"

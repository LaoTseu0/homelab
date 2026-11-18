# Déploiement — lab-studio

> Ansible déploie les fichiers de ce dossier sur `lab-studio`.

## Contenu

| Fichier | Déployé vers | Rôle |
|---|---|---|
| `docker-compose.yml` | `/srv/jarvis/` | Les 5 conteneurs (ollama, HA, whisper, piper, openwakeword) |
| `docker-compose.observability.yml` | `/srv/jarvis/` | Les 4 conteneurs d'observabilité, combinés au Compose principal |
| `observability/` | `/srv/jarvis/observability/` | Prometheus, provisioning Grafana et code de `jarvis-exporter` |
| `wyoming-satellite.service` | `/etc/systemd/system/` | Le satellite vocal en service systemd |
| `installer.sh` | — | Déploie les deux Compose et le satellite (idempotent) |

Les images officielles du pipeline vocal restent inchangées. L'observabilité
est un module séparé : arrêter ses quatre conteneurs ne coupe ni Home Assistant,
ni Ollama, ni les services Wyoming.

## Déployer le socle avec Ansible

Le [playbook de la tour](../../ansible/configurer-lab-studio.yml)
cible `lab-studio` via SSH avec le compte `studio`. Il prépare Docker et NVIDIA,
contrôle les montages des conteneurs existants, puis applique le Compose sous
`/srv/jarvis`. Le volume externe `ollama` et les chemins de données sous
`/srv/homeassistant` et `/srv/wyoming` servent à retrouver l’installation
actuelle. Sur une tour neuve, restaurer les données à ces emplacements avant
de lancer les services si l’objectif est de retrouver l’état précédent.

Depuis WSL, dans `ansible` avec l’environnement Ansible activé,
procède d’abord à une simulation sur la tour existante.

```bash
ansible-playbook -i inventory.yml configurer-lab-studio.yml --check --diff --ask-become-pass
```

Quand le Compose doit changer, la simulation affiche le diff du fichier et
reporte son application au passage réel. Avant la première reprise, faire une
sauvegarde de Home Assistant. Compose peut recréer les conteneurs dont la
configuration diffère, par exemple openWakeWord avec ses anciennes options de
debug. Lance ensuite la commande réelle, puis rejoue-la pour vérifier que la
configuration converge.

```bash
ansible-playbook -i inventory.yml configurer-lab-studio.yml --ask-become-pass
```

Le mot de passe demandé est celui de `sudo` pour `studio` sur la tour. Le
playbook installe l’unité Wyoming et la maintient arrêtée pendant que le
satellite est débranché. Après l’avoir rebranché, passe
`lab_studio_satellite_active` à `true` dans les
[variables de la tour](../../ansible/host_vars/lab-studio.yml) et
rejoue le playbook pour l’activer au démarrage et la lancer.

Le registre privé peut fournir chaque image publiée. Dans les mêmes variables,
ajoute les références au port `5001` épinglées par digest dans
`lab_studio_registry_images`, avec le nom de service Compose comme clé. À ce
moment-là, ajoute `--ask-vault-pass` à la commande. Ansible installe le
certificat public et utilise le compte de lecture déclaré sur le NAS.

### Publier les images de la reprise initiale

Le [script de publication](../../ansible/publier-images-lab-studio.sh)
reprend les images exactes d’Ollama, Home Assistant, Whisper, Piper et
openWakeWord. Les dépôts d’images de cette tour utilisent le préfixe `studio/`,
par exemple `studio/piper`. Lance le script depuis WSL, dans
`ansible`.

```bash
bash publier-images-lab-studio.sh
```

Le script transfère une archive temporaire vers le NVMe du NAS. Il publie les
images `linux/amd64` sur le port `5000` avec `publisher`, puis affiche les
références par digest pour le port `5001`. Le compte `pinas` fournit le
mot de passe sudo et `publisher` fournit le mot de passe Docker. Ajoute les
références affichées sous `lab_studio_registry_images`, y compris la nouvelle
référence de Piper, puis applique le playbook. À la fin de la publication,
le NAS supprime l’archive et garde le relevé des digests.

## Installateur avec observabilité

```bash
cd ~/homelab/deploiement/lab-studio
bash installer.sh
```

L'installateur combine automatiquement les deux fichiers :

```bash
docker compose --profile jarvis-exporter \
  -f /srv/jarvis/docker-compose.yml \
  -f /srv/jarvis/docker-compose.observability.yml \
  up -d
```

Il construit `jarvis-exporter`, provisionne Prometheus et Grafana, crée leurs
volumes persistants et conserve les secrets déjà présents. Les métriques sont
gardées 30 jours par Prometheus.

## Observabilité

### Activer la supervision de la tour avec Ansible

Prometheus collecte les métriques de `node-exporter`. Grafana affiche
le tableau **Lab Studio — CPU, RAM et disque**. Le déploiement d’apprentissage
sélectionne les fichiers de configuration et les tableaux adaptés à cette
collecte. Le profil Compose `jarvis-exporter` sert à l’observabilité applicative
de l’installateur complet.

1. Publier les versions `linux/amd64` de Prometheus, Grafana et Node Exporter
   sous `studio/` dans le registry du NAS. Renseigner les trois références
   du port `5001` par digest dans `lab_studio_monitoring_images`.
2. Préparer le compte Grafana `admin`. Dans WSL, depuis
   `ansible`, créer son fichier d’environnement chiffré. Si
   le fichier existe déjà, le conserver pour retrouver le même mot de passe.

```bash
grafana_env=../infra/secrets/lab-studio/grafana.env
if [[ ! -e "$grafana_env" ]]; then
  install -d -m 0700 "$(dirname "$grafana_env")" &&
    grafana_password=$(openssl rand -hex 24) &&
    printf 'GF_SECURITY_ADMIN_USER=admin\nGF_SECURITY_ADMIN_PASSWORD=%s\n' "$grafana_password" |
    ansible-vault encrypt --ask-vault-pass --output "$grafana_env" - &&
    printf 'Mot de passe Grafana à conserver\n%s\n' "$grafana_password"
  unset grafana_password
fi
```

Utiliser le même mot de passe Vault que pour le registry. Ansible déchiffre
le fichier pendant son transfert vers la tour et le protège avec le mode
`0600`. Le fichier chiffré reste dans `infra/secrets/` sur le PC admin.

3. Passer `lab_studio_observability_enabled` à `true` dans les variables
   de la tour et rejouer `configurer-lab-studio.yml` avec
   `--ask-become-pass --ask-vault-pass`. Le playbook vérifie que Prometheus
   collecte les métriques et que Grafana répond. Ouvrir Grafana sur le port
   `3000` de `lab-studio` et se connecter avec `admin`.

### Services et exposition réseau

| Service | Port | Exposition | Rôle |
|---|---:|---|---|
| Grafana | 3000 | LAN | Interface et dashboards |
| Prometheus | 9090 | `127.0.0.1` | Stockage et requêtes de métriques |
| `jarvis-exporter` | 9102 | `127.0.0.1` | Métriques Jarvis et benchmark manuel |
| node-exporter | 9100 | réseau Docker seulement | CPU, RAM, disque et réseau de l'hôte |

Le dashboard **Jarvis — observabilité** est provisionné automatiquement dans le
dossier Grafana `Jarvis`. Il regroupe machine, GPU, pipeline vocal et benchmarks
Ollama.

Les règles Prometheus détectent dès le départ :

- la disparition de `jarvis-exporter` ;
- une température GPU supérieure à 85 °C pendant 5 minutes ;
- un p95 du pipeline Assist supérieur à 4 secondes pendant 10 minutes.

Elles sont visibles dans Grafana/Prometheus. L'envoi d'une notification externe
reste à configurer une fois le canal choisi ; aucune action automatique n'arrête
la machine.

### Secrets

Au premier lancement, `installer.sh` crée sans les écraser ensuite :

```text
/srv/jarvis/secrets/grafana.env
/srv/jarvis/secrets/jarvis-exporter.env
```

Les secrets restent séparés : Grafana ne reçoit pas le jeton Home Assistant et
`jarvis-exporter` ne reçoit pas le mot de passe Grafana. Pour activer la collecte
passive des traces Assist :

1. créer dans Home Assistant un jeton longue durée pour un compte administrateur ;
2. renseigner `HOME_ASSISTANT_TOKEN` dans `jarvis-exporter.env` ;
3. relancer `./installer.sh` ou uniquement `docker restart jarvis-exporter`.

`HOME_ASSISTANT_PIPELINE_IDS` peut contenir une liste d'identifiants séparés par
des virgules. Vide, le collecteur découvre tous les pipelines. Ni les prompts,
ni les transcriptions, ni les réponses ne sont placés dans les métriques.

### Benchmark Ollama manuel

Aucune requête de benchmark n'est planifiée. Depuis une session SSH sur
`lab-studio` :

```bash
curl -sS -X POST http://127.0.0.1:9102/benchmark/ollama \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "Réponds en une phrase : quel est ton rôle ?",
    "num_predict": 64,
    "temperature": 0
  }'
```

Le résultat contient notamment le temps total vu par le client, le temps jusqu'au
premier token, les durées internes Ollama et les tokens par seconde. La réponse
est rendue au terminal mais n'est pas stockée dans Prometheus.

Limites de sécurité : `num_predict` vaut 64 par défaut et ne peut pas dépasser
256 sans modifier explicitement la configuration versionnée.

### Commandes utiles

```bash
# État de l'ensemble
docker compose --profile jarvis-exporter \
  -f /srv/jarvis/docker-compose.yml \
  -f /srv/jarvis/docker-compose.observability.yml \
  ps

# Logs de la collecte applicative
docker logs -f jarvis-exporter

# Vérifier les métriques et Prometheus depuis le serveur
curl http://127.0.0.1:9102/metrics
curl http://127.0.0.1:9090/-/healthy

# Arrêter uniquement l'observabilité, sans toucher au pipeline vocal
docker stop grafana prometheus node-exporter jarvis-exporter
```

Les données sont dans les volumes Compose `grafana-data` et `prometheus-data`.
Un `docker compose down` les conserve ; ne pas utiliser `down -v` sauf volonté
explicite d'effacer l'historique.

## Reconstruire le serveur de zéro

1. Refaire le socle : [../../serveurs/lab-studio/installation.md](../../serveurs/lab-studio/installation.md)
   (OS, drivers NVIDIA, Docker, NVIDIA Container Toolkit, alsa-utils).
2. Cloner ce repo depuis le NAS : `git clone nas:/srv/git/homelab.git ~/homelab`
3. `cd ~/homelab/deploiement/lab-studio && bash installer.sh`
4. Restaurer/refaire la config HA (`/srv/homeassistant` — backup au backlog),
   renseigner le nouveau jeton Home Assistant dans le fichier de secrets, et
   vérifier le numéro de carte ALSA du XVF3800 (`arecord -l`).

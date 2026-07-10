# Déploiement — jarvis-central

> Config déployable de la machine. **Source de vérité** : ce dossier ;
> le serveur n'en reçoit que des copies via `installer.sh`.
> Ne jamais éditer directement sur le serveur.

## Contenu

| Fichier | Déployé vers | Rôle |
|---|---|---|
| `docker-compose.yml` | `/srv/jarvis/` | Les 5 conteneurs (ollama, HA, whisper, piper, openwakeword) |
| `wyoming-satellite.service` | `/etc/systemd/system/` | Le satellite vocal en service systemd |
| `installer.sh` | — | Déploie tout (idempotent) |

## Déployer (ou re-déployer après un git pull)

```bash
cd ~/homelab/deploiement/jarvis-central
./installer.sh
```

## Reconstruire le serveur de zéro

1. Refaire le socle : [../../serveurs/jarvis-central/installation.md](../../serveurs/jarvis-central/installation.md)
   (OS, drivers NVIDIA, Docker, NVIDIA Container Toolkit, alsa-utils).
2. Cloner ce repo depuis le NAS : `git clone nas:/srv/git/homelab.git ~/homelab`
3. `cd ~/homelab/deploiement/jarvis-central && ./installer.sh`
4. Restaurer/refaire la config HA (`/srv/homeassistant` — backup au backlog),
   et vérifier le numéro de carte ALSA du XVF3800 (`arecord -l`).

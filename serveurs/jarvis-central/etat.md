# jarvis-central — état courant

> Photographie du serveur `jarvis-central` : le socle système, les services
> qui tournent dessus, où vit chaque chose et pourquoi : [installation](installation.md), [architecture](../../architecture/jarvis.md), [securite](../../architecture/securite.md).
> Dernière mise à jour : 10 juillet 2026
> Statut : **Phase 0 terminée** 🎉 — boucle vocale complète validée
> (« Hey Jarvis » → Whisper → Qwen3 → Piper → enceinte), 100 % local

---

## 1. État du socle

```
Ubuntu Server 26.04 LTS (headless, SSH)
 ├── Driver NVIDIA (RTX 2060 visible : nvidia-smi)
 │    └── Docker (groupe docker → sans sudo)
 │         └── NVIDIA Container Toolkit (--gpus all fonctionnel)
 │              ├── [conteneur] ollama          (port 11434, GPU)
 │              ├── [conteneur] homeassistant   (port 8123, network host)
 │              ├── [conteneur] whisper         (port 10300, STT, CPU)
 │              ├── [conteneur] piper           (port 10200, TTS, CPU)
 │              └── [conteneur] openwakeword    (port 10400, wake word, CPU)
 └── wyoming-satellite (sur l'hôte, port 10700 — exception justifiée, §2.4)
```

Règle : tout service de Jarvis est un conteneur posé sur ce socle — rien
n'est installé directement sur l'hôte à part le driver GPU, Docker,
`alsa-utils` et **une exception documentée** (wyoming-satellite, §2.4).
Le détail des emplacements disque est en §4.

**Les 5 conteneurs sont gérés par docker compose** : 
-  [docker-compose.yml](../../deploiement/jarvis-central/docker-compose.yml) versionné dans [deploiement/jarvis-central/](../../deploiement/jarvis-central/)
est la source de vérité 
-  il est copié vers `/srv/jarvis/` par [installer.sh](../../deploiement/jarvis-central/installer.sh). 
-  Les commandes `docker run` détaillées plus bas sont leurs équivalents unitaires, gardées
pour expliquer chaque option.

```bash
cd /srv/jarvis
docker compose up -d      # (re)lance tout le corps de Jarvis
docker compose pull && docker compose up -d   # met tout à jour
docker compose down       # arrête tout
```

Les données vivent hors des conteneurs (volume `ollama`, `/srv/homeassistant`,
`/srv/wyoming/`) : détruire/recréer les conteneurs ne perd rien.

---

## 2. Services en place

### 2.1 Ollama — moteur LLM (port 11434)

Service **neutre et partagé** : premier client = Home Assistant (raisonnement
vocal) ; plus tard, la couche agentique (Hermes/Pi) pourra l'appeler
directement. Ce n'est pas « l'outil de HA », c'est le moteur commun.

**Lancement du conteneur :**

```bash
docker run -d --gpus all \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  --restart unless-stopped \
  --name ollama \
  ollama/ollama
```

- `--gpus all` : accès à la RTX 2060 via le NVIDIA Container Toolkit.
- `-v ollama:/root/.ollama` : volume persistant pour les modèles (survit aux
  mises à jour du conteneur).
- `-p 11434:11434` : expose l'API — c'est par ce port que HA (et plus tard
  l'agent) parlent au LLM.
- `--restart unless-stopped` : redémarre avec la machine.

**Modèles installés :**

```bash
docker exec ollama ollama pull qwen3:4b-instruct-2507-q4_K_M
docker exec ollama ollama pull nomic-embed-text
```

**Qwen3 4B Instruct 2507** (quantization q4_K_M, ~2,5 Go) :
- variante **non-thinking** (pas de blocs `<think>` — indispensable en voix) ;
- **tool calling** (pilotage des entités HA) ;
- ~3 Go de VRAM occupés → laisse de la marge sur les 6 Go pour la suite.

**nomic-embed-text** (~270 Mo) : modèle d'**embeddings** (texte → vecteur,
pas de génération) pour le RAG sur la doc du homelab (formation module 2).
Endpoint `/api/embed` ; ne monopolise pas la VRAM en dehors des appels.

**Tests de validation :**

```bash
# Chat interactif dans le terminal (quitter avec /bye)
docker exec -it ollama ollama run qwen3:4b-instruct-2507-q4_K_M

# Test de l'API (celle qu'utilise HA)
curl http://localhost:11434/api/generate -d '{
  "model": "qwen3:4b-instruct-2507-q4_K_M",
  "prompt": "Dis bonjour en une phrase.",
  "stream": false
}'
```

✅ Validé : ~95 tokens/s (signature GPU — sur CPU un 4B ferait 10-20 tok/s),
réponse totale < 0,5 s. Le LLM ne sera pas le goulot du pipeline vocal.

### 2.2 Home Assistant — chef d'orchestre voix/domotique (port 8123)

Rôle : **standard téléphonique**, pas l'intelligence. Il reçoit l'audio des
futurs satellites (Wyoming), traite lui-même les commandes simples
(intents locaux ~200 ms), délègue le raisonnement à Ollama, et gérera la
domotique (Zigbee, entités, automatisations).

**Lancement du conteneur :**

```bash
docker run -d \
  --name homeassistant \
  --restart unless-stopped \
  --privileged \
  -e TZ=Europe/Paris \
  -v /srv/homeassistant:/config \
  --network host \
  ghcr.io/home-assistant/home-assistant:stable
```

- `-v /srv/homeassistant:/config` : toute la config HA vit sur l'hôte dans
  `/srv/homeassistant` (cible des futurs backups).
- `--network host` : nécessaire pour la découverte mDNS et les satellites
  Wyoming.
- `TZ=Europe/Paris` : automatisations à l'heure locale.

**Interface web** : `http://<IP-du-serveur>:8123`

**Configuration effectuée (via l'interface) :**

1. Compte administrateur créé.
2. Intégration **Ollama** ajoutée (Paramètres → Appareils et services) —
   URL `http://127.0.0.1:11434`, modèle `qwen3:4b-instruct-2507-q4_K_M`,
   contrôle de HA (tool calling) activé.
3. Assistant **« Jarvis »** créé (Paramètres → Assistants vocaux) — langue
   **français** (conditionne les intents locaux et la langue de Whisper),
   agent de conversation = Ollama.
4. **Instructions personnalisées** (intégration Ollama → « Configurer » →
   champ « Instructions ») : le template par défaut étant en anglais, le 4B
   répondait en anglais. Consigne ajoutée en tête du template :
   > Tu es Jarvis, l'assistant vocal de la maison. Réponds toujours en
   > français, de façon brève et directe (tes réponses sont lues à voix
   > haute).
   Les réponses courtes comptent : chaque phrase sera prononcée par Piper.

✅ Validé : conversation en texte via le chat Assist (bulle en haut à droite),
réponse en ~1 s, modèle bien chargé en VRAM pendant la génération.

### 2.3 Briques Wyoming — les oreilles, la bouche et le réveil

Trois services distincts reliés à HA par le protocole **Wyoming** (une
intégration « Wyoming Protocol » par service, hôte `127.0.0.1`).
Tous tournent sur **CPU** (Ryzen 5 + 32 Go) pour garder la VRAM au LLM.

**faster-whisper — STT, voix → texte (port 10300) :**

```bash
docker run -d --name whisper --restart unless-stopped \
  -p 10300:10300 \
  -v /srv/wyoming/whisper:/data \
  rhasspy/wyoming-whisper \
  --model small-int8 --language fr
```

**Piper — TTS, texte → voix (port 10200) :**

```bash
docker run -d --name piper --restart unless-stopped \
  -p 10200:10200 \
  -v /srv/wyoming/piper:/data \
  rhasspy/wyoming-piper \
  --voice fr_FR-siwis-medium
```

**openWakeWord — détection de « Hey Jarvis » (port 10400) :**

```bash
docker run -d --name openwakeword --restart unless-stopped \
  -p 10400:10400 \
  rhasspy/wyoming-openwakeword \
  --preload-model 'hey_jarvis'
```

> openWakeWord n'apparaît pas comme « marque » propre dans HA : les trois
> briques s'ajoutent via la même intégration **Wyoming Protocol** (ports
> 10300 / 10200 / 10400). Le wake word se choisira au niveau de chaque
> satellite, pas dans la config de l'assistant.

**Configuration de l'assistant** (Paramètres → Assistants vocaux → Jarvis) :
Voix → texte = faster-whisper, Texte → voix = piper
(voix `fr_FR-siwis-medium`).

> Politique de redémarrage : tous les conteneurs sont en `--restart
> unless-stopped` → tout revient seul après reboot ou coupure de courant
> (couplé au réglage BIOS « Power On after AC loss »). Un conteneur arrêté
> à la main reste arrêté.

### 2.4 wyoming-satellite — le pont micro/enceinte → HA (port 10700)

⚠️ **Seule brique installée sur l'hôte, pas en conteneur.** Deux raisons :
l'image Docker officielle a un historique capricieux avec l'audio
(`/dev/snd`, alsa-utils manquants), et ce composant est **temporaire** sur
le serveur — en Phase 1, le satellite déménage sur le Pi 5 ou un ESP32.
Pas la peine d'industrialiser un banc d'essai.

**Matériel** : ReSpeaker **XVF3800 en USB** (variante USB Audio — question
ouverte n°1 de l'architecture **tranchée** : la carte apparaît dans `lsusb`
et comme carte ALSA nommée `Array`). Alimentée par le port USB, enceinte
branchée sur sa sortie audio (indispensable : l'annulation d'écho de la puce
XMOS doit « entendre » ce que l'enceinte joue).

**Installation** (méthode officielle du dépôt) :

```bash
sudo apt install -y python3-venv git
git clone https://github.com/rhasspy/wyoming-satellite.git ~/wyoming-satellite
cd ~/wyoming-satellite && script/setup
```

**Lancement** : service systemd
[`wyoming-satellite.service`](../../deploiement/jarvis-central/wyoming-satellite.service)
(versionné dans `deploiement/`, installé par `installer.sh`), qui exécute
`script/run` avec le micro/enceinte sur `plughw:CARD=Array,DEV=0` —
adressage **par nom**, robuste au changement d'ordre d'énumération des
cartes entre boots, contrairement au numéro (`plughw:2,0`). Wake word
délégué au conteneur openwakeword (10400), `Restart=always`.

```bash
systemctl status wyoming-satellite     # état
journalctl -u wyoming-satellite -f     # logs en direct
sudo systemctl restart wyoming-satellite
```

Le satellite capte le micro, envoie le flux au conteneur openwakeword
(10400) pour la détection, streame la suite vers HA, et joue la réponse.

**Côté HA** : intégration Wyoming Protocol (`127.0.0.1:10700`) → appareil
« bureau », traitement **local complet** (ni cloud, ni Speech-to-Phrase),
assistant Jarvis-HA, voix `siwis (medium)`.

✅ Validé : boucle complète « Hey Jarvis, c'est quoi l'hydrogène ? » →
réponse parlée dans l'enceinte, 100 % local. **Fin de la Phase 0.**

> Prononciation : le modèle `hey_jarvis` est entraîné sur des voix
> anglaises — « héï djarvis » passe bien mieux qu'un « hé Jarvis » à la
> française. Pour tout diagnostic :
> [guide de debug du pipeline vocal](../../guides/debug-pipeline-vocal.md).

---

## 3. Modèle mental — qui parle à qui

```
[ Satellite « bureau » ]
[ XVF3800 USB + enceinte ] ──audio/Wyoming──► [ Home Assistant :8123 ]
                                              │  commandes simples : intents
                                              │  locaux (~200 ms, sans LLM)
                                              │  raisonnement :
                                              ▼
                                            [ Ollama :11434 — Qwen3 4B ]
                                              ▲
[ Couche agentique Hermes/Pi (Phase 3) ] ─────┘  (appel direct, sans HA)
```

- Les satellites ne connaissent **que** HA.
- Ollama est le moteur commun des deux cerveaux.
- Le pont HA ↔ agent (MCP) viendra en Phase 3.

---

## 4. Organisation du disque — où vit quoi, et pourquoi là

Convention générale : **`/srv`** pour tout ce qui appartient aux *services*
de la machine (c'est son rôle dans le standard FHS : « données servies par
le système »), **`/home/jarvis`** pour ce qui est expérimental ou temporaire,
**volumes Docker** pour les données gérées par Docker qu'on n'a jamais
besoin de toucher directement. Même logique que le NAS (`/srv/git`,
`/srv/partages`).

| Emplacement | Contenu | Pourquoi là |
|---|---|---|
| `/srv/jarvis/docker-compose.yml` | Définition des 5 conteneurs | Config de service → `/srv` ; hors de `/home` car indépendante de tout utilisateur. **Copie** déployée par `installer.sh` — la source de vérité est `deploiement/jarvis-central/` dans ce repo. |
| `/etc/systemd/system/wyoming-satellite.service` | Service du satellite vocal | Emplacement imposé par systemd. **Copie** déployée par `installer.sh` — source de vérité dans le repo. |
| `/srv/homeassistant/` | Config complète de HA (bind mount `/config`) | Donnée de service critique → `/srv` ; en bind mount (pas en volume) pour être lisible, éditable et **sauvegardable** directement — c'est la cible n°1 des futurs backups. |
| `/srv/wyoming/whisper/`, `/srv/wyoming/piper/` | Modèles STT/TTS téléchargés (bind mounts `/data`) | Même logique : données de service, regroupées sous un parent `wyoming/` commun. Re-téléchargeables, mais autant ne pas le refaire à chaque recréation de conteneur. |
| volume Docker `ollama` | Modèles LLM (~Go de blobs binaires) | Volume nommé géré par Docker : aucun besoin d'accès direct par l'humain, contenu re-téléchargeable à l'identique (`ollama pull`). Exception assumée à la règle bind mount. |
| `/home/jarvis/wyoming-satellite/` | Clone git + venv du satellite | Composant **temporaire** (part sur Pi 5/ESP32 en Phase 1) et installé hors Docker → statut expérimental, donc `/home` et pas `/srv`. S'il devenait permanent, il faudrait le promouvoir (conteneur ou `/srv` + systemd). |
| `/home/jarvis/homelab/` | Clone du repo `homelab.git` (NAS, compte `jarvisc`) | Point d'entrée du déploiement : `git pull` puis `deploiement/jarvis-central/installer.sh`. Dans `/home` car c'est une copie de travail, pas une donnée de service — les copies déployées, elles, vont dans `/srv` et `/etc`. |
| `/etc/docker/daemon.json` | Déclaration du runtime NVIDIA à Docker | Généré par `nvidia-ctk runtime configure` — config système, emplacement imposé. |
| `/etc/apt/sources.list.d/*.list`, `/usr/share/keyrings/*.gpg` | Dépôts apt Docker et NVIDIA + leurs clés | Emplacements standard d'apt pour les dépôts tiers signés. |

Corollaire important : **les conteneurs sont jetables, ces emplacements ne le
sont pas.** `docker rm` / recréation / mise à jour ne touchent à rien de
cette table. Ce qui doit être sauvegardé un jour : `/srv/homeassistant`
(critique, non reconstructible) ; tout le reste se retélécharge ou se
reclone.

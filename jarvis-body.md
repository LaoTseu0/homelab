# Jarvis Body — le corps principal du setup

> État courant du serveur `jarvis-central` : le socle système et les services
> qui tournent dessus. C'est la photographie du « corps » de Jarvis — ce qui
> est installé, comment, et pourquoi.
> L'installation du socle lui-même est décrite dans
> [installation-serveur-jarvis.md](installation-serveur-jarvis.md) ;
> l'architecture cible dans [jarvis-maison-architecture.md](jarvis-maison-architecture.md).
> Dernière mise à jour : 10 juillet 2026
> Statut : **pipeline vocal complet côté serveur** (STT + LLM + TTS + wake
> word branchés dans HA), géré en config-as-code via docker compose — il ne
> manque que les oreilles physiques (satellite)

---

## 1. État du socle

```
Ubuntu Server 26.04 LTS (headless, SSH)
 └── Driver NVIDIA (RTX 2060 visible : nvidia-smi)
      └── Docker (groupe docker → sans sudo)
           └── NVIDIA Container Toolkit (--gpus all fonctionnel)
                ├── [conteneur] ollama          (port 11434, GPU)
                ├── [conteneur] homeassistant   (port 8123, network host)
                ├── [conteneur] whisper         (port 10300, STT, CPU)
                ├── [conteneur] piper           (port 10200, TTS, CPU)
                └── [conteneur] openwakeword    (port 10400, wake word, CPU)
```

Tout service de Jarvis est un conteneur posé sur ce socle — rien n'est
installé directement sur l'hôte à part Docker et le driver GPU.

**Les 5 conteneurs sont gérés par docker compose** : le fichier
[docker-compose.yml](docker-compose.yml) (versionné dans ce repo, copie sur
le serveur dans `/srv/jarvis/`) est la source de vérité. Les commandes
`docker run` détaillées plus bas sont leurs équivalents unitaires, gardées
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

**Modèle installé :**

```bash
docker exec ollama ollama pull qwen3:4b-instruct-2507-q4_K_M
```

**Qwen3 4B Instruct 2507** (quantization q4_K_M, ~2,5 Go) :
- variante **non-thinking** (pas de blocs `<think>` — indispensable en voix) ;
- **tool calling** (pilotage des entités HA) ;
- ~3 Go de VRAM occupés → laisse de la marge sur les 6 Go pour la suite.

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

---

## 3. Modèle mental — qui parle à qui

```
[ Satellites (à venir) ] ──audio/Wyoming──► [ Home Assistant :8123 ]
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

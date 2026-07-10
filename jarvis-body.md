# Jarvis Body — le corps principal du setup

> État courant du serveur `jarvis-central` : le socle système et les services
> qui tournent dessus. C'est la photographie du « corps » de Jarvis — ce qui
> est installé, comment, et pourquoi.
> L'installation du socle lui-même est décrite dans
> [installation-serveur-jarvis.md](installation-serveur-jarvis.md) ;
> l'architecture cible dans [jarvis-maison-architecture.md](jarvis-maison-architecture.md).
> Dernière mise à jour : 10 juillet 2026
> Statut : **cerveau LLM opérationnel, validé en texte via Home Assistant**

---

## 1. État du socle

```
Ubuntu Server 26.04 LTS (headless, SSH)
 └── Driver NVIDIA (RTX 2060 visible : nvidia-smi)
      └── Docker (groupe docker → sans sudo)
           └── NVIDIA Container Toolkit (--gpus all fonctionnel)
                ├── [conteneur] ollama          (port 11434, GPU)
                └── [conteneur] homeassistant   (port 8123, network host)
```

Tout service de Jarvis est un conteneur posé sur ce socle — rien n'est
installé directement sur l'hôte à part Docker et le driver GPU.

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
   français, agent de conversation = Ollama. STT/TTS vides pour l'instant
   (briques Wyoming pas encore installées).

✅ Validé : conversation en texte via le chat Assist (bulle en haut à droite),
réponse en ~1 s, modèle bien chargé en VRAM pendant la génération.

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

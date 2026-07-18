# Projet Jarvis Maison — Architecture & Feuille de route

> **Rôle de ce document** : base de connaissances de référence pour l'assistant
> vocal + agentique domestique auto-hébergé (« Jarvis »). Contexte projet pour
> agents/Claude, pensé pour vivre dans git (à côté de `archi-maison.git` /
> `homelab.git` / `memoire-agent.git` sur le NAS).
>
> **Dernière mise à jour** : 18 juillet 2026 — **v3**
> **Statut global** : **Phase 0 terminée** — boucle vocale complète validée sur
> `jarvis-central` (voir [../serveurs/jarvis-central/etat.md](../serveurs/jarvis-central/etat.md)).
> Tour d'inférence `jarvis-core` (RTX 4090) en préparation — voir
> [inference.md](inference.md).

---

## 1. Objectif

Assistant personnel de type « Jarvis », **100 % local** (aucun audio ne quitte la
maison), vocal et multi-pièces, avec **deux missions** :

1. **Voix + domotique** : piloter la maison, répondre aux questions courantes.
2. **Assistant de tâches informatiques** : aide au dev (ex. Three.js), actions sur
   le homelab, orchestration de fichiers/scripts.

Pas de LLM cloud au démarrage. Option gardée en *fallback* pour les tâches lourdes.

---

## 2. Principe directeur

1. **Incrémental** : petit d'abord, une brique testable à la fois, quitte à
   sacrifier des perfs.
2. **DIY & communauté** : stack éprouvée Home Assistant / maker (Wyoming, Whisper,
   Piper, Ollama, ESPHome) + écosystème agent 2026 (Hermes/Pi, OKF).
3. **Tout sur le vieux PC gamer d'abord**, puis **export** vers matériel dédié.
4. **Scale vertical** : priorité à la puissance du « cerveau » (GPU/VRAM) avant la
   multiplication des pièces.
5. **Markdown + git partout** : mémoire, config, veille — versionnées, portables.
6. **Cloisonnement & sécurité** : conteneurs, moindre privilège, rien exposé au web.

---

## 3. Architecture cible — modèle « deux cerveaux + mémoire partagée »

Insight central : le pilotage voix/domotique et l'assistant de tâches sont **deux
couches distinctes et complémentaires**, reliées par **MCP**, partageant une
**mémoire markdown/git** commune.

```
   CERVEAU VOIX/DOMOTIQUE            CERVEAU AGENTIQUE / TÂCHES
   Home Assistant + Assist          Hermes Agent (ou Pi)
   Ollama (Qwen3 4B, tool calling)  actions homelab / dev / scripts
        │                                   │
        └──────────────── MCP ──────────────┘
                          │
              MÉMOIRE PARTAGÉE (fichiers .md, convention OKF)
              édition humaine : Obsidian │ versioning : git (NAS)
              (évolution de memoire-agent.git → jarvis-memory)
```

- **HA + Ollama** = réactif, borné aux entités domotiques (rapide, tool calling).
- **Hermes/Pi** = autonome, accès outils/fichiers, mémoire longue, *self-improving*.
- **MCP** = le pont : HA peut exposer un serveur MCP ; l'agent appelle ses outils.
- **Mémoire** = substrat commun lisible par les deux (et par toi).

### Pipeline vocal (détail du cerveau voix)

```
[ Satellite pièce ]  micro + enceinte
   wake word local ("Hey Jarvis")  ──WiFi/Wyoming──►  [ Cerveau PC ]
                                                        Home Assistant
   ┌──────────────┬───────────────────────────┬─────────────────┐
   ▼              ▼                           ▼                 ▼
 faster-whisper  intents natifs HA          Ollama (LLM)      Piper (TTS)
 (STT)           (prefer_local_intents)     si raisonnement   texte→voix
                 "allume la lumière" ~200ms  requis                │
                                                                   ▼
                                             réponse renvoyée au bon satellite
```

**Règle d'or : `prefer_local_intents`.** HA traite les commandes simples en
~200 ms sans réveiller le LLM ; le LLM n'intervient que pour le raisonnement.

---

## 4. Matériel

### Inventaire réel

| Élément | Détail | Rôle Jarvis |
|---|---|---|
| **`jarvis-central`** (vieux PC gamer) | **RTX 2060 6 Go**, 32 Go RAM, Ryzen 5 | **Cerveau voix/domotique** (HA + Ollama + Whisper + Piper) — front door 24/7 |
| **`jarvis-core`** (tour) | **RTX 4090 24 Go**, 64 Go RAM | **Moteur d'inférence LLM dédié** — en préparation, voir [inference.md](inference.md) |
| Raspberry Pi 4 8 Go | **= NAS** (git + SMB), actif | Occupé — ne pas réquisitionner (avec SSD Kingston 250 Go en backup) |
| Raspberry Pi 5 8 Go | libre | **Satellite** ou hôte add-ons vocaux (ReSpeaker XVF3800 prévu) |
| `pc-admin` (PC portable Asus ROG) | PC perso | Administration du homelab (étage) |

### Lecture de la RTX 2060 (6 Go) — ce qui rentre

| Modèle | VRAM | Verdict |
|---|---|---|
| **Qwen3 4B Instruct** (tool calling) | ~3–4 Go | ✅ **Départ recommandé** (laisse la place à Whisper) |
| faster-whisper small/base (int8) | ~1–2 Go | ✅ sur GPU, ou sur **CPU** (Ryzen 5 + 32 Go) |
| Piper (TTS) | CPU | ✅ trivial |
| Gemma 4 12B Q4 | ~6 Go | ⚠️ remplit la carte, rien pour Whisper en //→ *plus tard* |
| Modèles 20–30B | >12 Go | ❌ hors 6 Go (cible d'un futur GPU) |

> **6 Go = OK pour la domotique.** Pour le **dev Three.js**, un 4B local est
> faible → c'est le rôle de **`jarvis-core`** (RTX 4090, voir
> [inference.md](inference.md)). Comme Hermes/Pi sont *model-agnostic*, on
> route les tâches lourdes vers jarvis-core sans ré-architecturer. Le
> **CPU + 32 Go de RAM** est un atout : inférence CPU de secours,
> Whisper/Pyannote sur CPU si besoin.

---

## 5. Stack logicielle (consensus communauté 2026)

| Brique | Outil | Notes |
|---|---|---|
| Orchestration voix | **Home Assistant** (Assist + Wyoming) | Intégration **Ollama native** depuis 2024.4 |
| Wake word | **micro_wake_word** (sur ESP32) / **openWakeWord** (serveur) | « Hey Jarvis » dispo, détecté sur puce |
| STT | **faster-whisper** (GPU/CPU) | Sur Pi → *Speech-to-Phrase* (Whisper trop lent sur Pi) |
| LLM voix | **Ollama** + **Qwen3 4B** (tool calling) | Éviter les modèles *think-mode* (trop lents) |
| TTS | **Piper** | Streaming → réponse quasi instantanée |
| Protocole | **Wyoming** | Relie STT/TTS/wake word ; chaque brique = service séparé |
| Agent de tâches | **Hermes Agent** (ou **Pi**) | Couche agentique, voir §7 |
| Mémoire | **.md OKF + Obsidian + git** | Voir §6 |
| Domotique | **Zigbee** (mûr) puis **Matter/Thread** | Voir §8 |

---

## 6. Couche mémoire persistante (OKF + Obsidian + git)

**Constat** : `memoire-agent.git` est déjà, de fait, une « LLM-wiki » — le pattern
que Google a formalisé.

- **OKF (Open Knowledge Format)** — publié par Google Cloud le **12 juin 2026**.
  Un répertoire de **fichiers markdown + frontmatter YAML**, un concept par
  fichier, seul le champ `type` requis. Vendor-neutral, sans SDK, git-friendly.
  **Complète MCP** (MCP = accès outils/données ; OKF = la connaissance elle-même).
- **Obsidian** — éditeur/visualiseur humain (graphe de liens) par-dessus les mêmes
  `.md`. Pratique pour naviguer/écrire à la main.
- **git (NAS)** — versioning + synchro, dans la lignée de l'existant.
- **Exposition aux agents** — via **MCP** ou lecture directe des fichiers.

**Mise en œuvre pragmatique** :
- Créer un dépôt `jarvis-memory` (ou réutiliser `memoire-agent.git`).
- Adopter la convention OKF **légèrement** (frontmatter `type/title/tags/timestamp`)
  — OKF est en v0.1, « point de départ », inutile de sur-ingénierier.
- Y ranger : préférences, profils (voir diarisation §9), état domotique, notes de
  veille (§10), décisions d'archi.

Exemple de note :
```markdown
---
type: Device
title: Lampe salon
tags: [domotique, salon, zigbee]
timestamp: 2026-07-01
---
Ampoule Zigbee pilotable par voix. Alias Assist : « lampe salon ».
```

---

## 7. Couche agentique / orchestration

⚠️ **Distinct de HA+Ollama** (qui est la voix/domotique). Ici : agent autonome pour
le dev, les actions homelab, l'orchestration.

| Option | Nature | Pour toi |
|---|---|---|
| **Hermes Agent** (Nous Research, févr. 2026) | Agent autonome persistant, auto-hébergé, mémoire profonde, *self-improving*, **model-agnostic**. « Profile » = **dépôt git** (identité complète : skills, providers, MCP, cron). Peut agir comme serveur MCP. | ✅ **Le plus aligné** (git-natif, modèles locaux, sandbox) |
| **Pi (pi.dev)** | Harnais d'agent de **code** minimal (4 outils, MIT, Mario Zechner). OpenClaw bâti sur son SDK. Extensions multi-agent (teams/chains/pipelines en YAML+md). | ✅ Si focus **dev/coding** |
| **OpenClaw** | Bâti sur Pi, viral, mais **cauchemar sécurité** (≈138 CVE début 2026). | ❌ Éviter, ou lourdement sandboxé |

### 🔒 Sécurité (non négociable)

Un agent autonome avec `bash` sur la box homelab (SSH, git, fichiers d'Océane) =
risque réel.
- **Moindre privilège** + **sandbox** + conteneur dédié.
- **Aucun outil destructif** sans validation humaine (redémarrages, `rm`, `sudo`…).
- **Rien exposé à Internet** (cohérent avec le réseau local-only).
- Les patterns « pré-hook qui bloque les commandes destructrices » (cf. agent-pi,
  roach-pi) sont un bon modèle.

**Reco** : Jarvis persistant git-natif → **Hermes** ; focus dev → **Pi**. Router les
tâches lourdes vers un plus gros modèle plus tard (sans ré-archi, car agnostique).

---

## 8. Satellites & protocoles domotiques

### Satellites vocaux

- **XVF3800** (déjà là) : meilleur far-field (4 micros XMOS) → pièces exigeantes
  (salon). Nécessite firmware + enceinte + boîtier 3D ; **loin de la TV**.
- **ESP32-S3** : la puce de référence pour un satellite vocal/écran, wake word
  « Hey Jarvis » **sur la puce**. ~4–15 €. Idéal pièces secondaires.
- **ESP32-S3-BOX-3** : clé-en-main (écran + HP + micro, firmware HA officiel,
  ~15 min). Micros corrects mais **moins bons en champ lointain** que le XVF3800.

### Protocoles (couche domotique, **côté serveur HA**)

Le satellite n'est qu'un **point audio** ; Matter, Zigbee, Thread, Z-Wave vivent
sur l'hôte HA — indépendants de la voix.

- **⚠️ Choix de puce ESP32 selon l'usage** : S3 pour voix/écran/audio ; **C6 ou H2
  pour Thread/Matter** (seuls à avoir la radio 802.15.4).
- **Matter/Thread** : l'avenir, mais encore « early adopter » (multicast IPv6,
  commissioning capricieux). Nécessite un *Thread Border Router*.
- **Zigbee** (via un coordinateur type ZBT/SkyConnect) : **le plus mûr** → défaut
  pragmatique pour démarrer, on ajoute du Matter au fur et à mesure.

---

## 9. Diarisation / reconnaissance du locuteur

**Statut : avancé, non standard, R&D (après le socle).**
- Le XVF3800 fait de la **DoA** (direction), pas de l'identité.
- HA Assist ne fait **pas** de speaker-ID nativement → service custom (Pyannote)
  en amont du LLM. À faire tourner sur **GPU/CPU du PC**, pas sur un Pi.
- Empreinte vocale ~30 s / personne. Profils stockés dans la mémoire markdown (§6).
- Le multi-satellite HA répond déjà « à la bonne pièce » sans savoir qui parle.

---

## 10. Veille communauté (« Jarvis+ »)

À suivre et à **consigner dans le vault Obsidian** (note OKF `type: watch` par
techno — la veille devient de la mémoire agent) :
- **HA / voix** : r/homeassistant, forum HA (section Voice), blog HA (« Voice
  Chapter », « Meet Nabu »), communauté ESPHome, wiki Seeed.
- **LLM local** : r/LocalLLaMA, releases Ollama, familles Qwen3 / Gemma 4.
- **Agents** : dépôts GitHub Pi (badlogic/earendil), Hermes (Nous Research),
  annonces OKF ; r/selfhosted.
- **Sécurité** : suivre les CVE des frameworks agentiques avant de les exposer.

---

## 11. Feuille de route incrémentale

### Phase 0 — Socle voix tout-en-un (vieux PC)
- [ ] Installer **Home Assistant** (VM/OS, ou Container) sur le PC.
- [ ] Add-ons **faster-whisper**, **Piper**, **openWakeWord** (Wyoming).
- [ ] **Ollama** + **Qwen3 4B** (tool calling). **Tester en texte** (chat Assist).
- [ ] `prefer_local_intents` ON ; exposer 5–10 entités.
- [ ] 1er test vocal : XVF3800 en **USB** sur le PC ; wake word « Hey Jarvis ».

### Phase 1 — 1er satellite (salon)
- [ ] Confirmer la **variante XVF3800** (USB vs ESP32-S3/ESPHome).
- [ ] Monter le satellite (ESPHome WiFi **ou** USB sur Pi 5) + enceinte + boîtier 3D.
- [ ] **Éloigner de la TV.** Valider la boucle salon→PC→salon.

### Phase 2 — Mémoire + durcissement
- [ ] Dépôt **`jarvis-memory`** (convention OKF) + **Obsidian** + git NAS.
- [ ] **IP fixes** (réservation DHCP) pour PC-cerveau et satellites.
- [ ] Conteneurisation + **user HA limité** + system prompt protecteur.
- [ ] **Backup** config HA (SSD + rsync/cron).

### Phase 3 — Couche agentique
- [ ] Installer **Hermes** (ou Pi) **sandboxé**, sans outil destructif.
- [ ] Relier à HA via **MCP** ; brancher la mémoire markdown.
- [ ] Premiers workflows (aide dev, actions homelab supervisées).

### Phase 4 — Extension & R&D
- [ ] Multi-pièces (ESP32-S3-BOX secondaires) + écran salon.
- [ ] Domotique (Zigbee puis Matter/Thread).
- [ ] **Scale vertical** : brancher Jarvis sur `jarvis-core` (RTX 4090) →
      modèle plus fort (voir [inference.md](inference.md)).
- [ ] **Diarisation** (Pyannote) — expérimental.
- [ ] Option **fallback cloud** pour tâches lourdes (Three.js/code).

---

## 12. Évolutions envisagées (au-delà de la roadmap)

Idées structurantes, non planifiées, à ne pas perdre. Règle : rien dans
l'architecture actuelle ne doit **fermer** ces portes.

### Routeur multi-modèles (orchestrateur vocal)

Remplacer à terme le pipeline linéaire (wake → STT → LLM → TTS) par un
**aiguilleur** placé devant HA : demande légère → modèle **audio-natif**
(speech-to-speech, sans passage par le texte, réponse fluide et
« humaine ») ; demande technique → STT + LLM de réflexion ; commande
domotique → délégation à HA (API/MCP).

→ Conception détaillée : **[router-multi-model.md](router-multi-model.md)**

Pourquoi c'est compatible avec l'existant : les satellites parlent Wyoming
(protocole ouvert) et se fichent de qui les écoute ; HA resterait le
back-end domotique ; seule la couche d'orchestration serait remplacée.
Prérequis matériel : les modèles audio-natifs locaux (Moshi, Qwen-Omni…)
dépassent les 6 Go de VRAM → les 24 Go de `jarvis-core` lèvent ce blocage
(voir [inference.md](inference.md)).

---

## 13. Points de vigilance

- **6 Go de VRAM** : bon pour domotique, faible pour dev complexe → Qwen3 4B
  pour la voix, les tâches lourdes vers `jarvis-core` ([inference.md](inference.md)).
- **Pi 4 8 Go = NAS** (occupé). Satellite = Pi 5 libre / ESP32 / achat.
- **Whisper sur Pi = trop lent** (~8 s) → STT sur le PC (GPU/CPU).
- **Lien RDC↔étage en WiFi** : débit OK (audio léger), fiabilité à surveiller
  (Ethernet/CPL à terme — déjà dans la roadmap homelab).
- **Conso 24/7** : un vieux PC gamer tire bien plus qu'un Pi (50–100 W+ vs 3–5 W).
  OK pour tester ; argument pour migrer le cerveau vers de l'efficient à terme.
- **Agents autonomes = risque sécurité** : sandbox, moindre privilège, pas
  d'outil destructif, rien exposé au web. OpenClaw à éviter en l'état.
- **XVF3800** : firmware + enceinte + boîtier ; **loin de la TV**.
- **Modèle sans tool calling / think-mode = inutilisable** en voix.
- **Backup** config HA + mémoire (même risque que le NAS microSD sans backup).
- **Matter** = early adopter (IPv6 multicast, commissioning) → Zigbee pour démarrer.

---

## 14. Questions ouvertes

1. Emplacement physique : PC-cerveau (étage ?) et satellite salon (distance TV).
2. **Hermes ou Pi** pour la couche agentique (selon le poids dev vs domotique) ?
3. Les questions d'inférence de `jarvis-core` (modèle, serveur, alimentation) :
   voir [inference.md](inference.md) §6.

> Tranchées depuis la v2 : la **variante du XVF3800** (→ USB Audio, voir
> [etat.md §2.4](../serveurs/jarvis-central/etat.md)) et **HA en VM vs
> conteneur** (→ conteneur Docker, voir
> [installation.md](../serveurs/jarvis-central/installation.md)).

---

## 15. Glossaire

- **Assist / Wyoming** : pipeline vocal HA / protocole reliant wake word, STT, TTS.
- **STT / TTS** : voix→texte / texte→voix (faster-whisper / Piper).
- **Speech-to-Phrase** : STT fermé, quasi instantané, adapté Pi.
- **Ollama** : hébergeur de LLM locaux, intégration native HA.
- **Tool calling** : capacité d'un LLM à appeler des outils (piloter HA).
- **micro_wake_word** : détection du mot de réveil sur la puce ESP32.
- **DoA** : direction d'arrivée du son (≠ identité du locuteur).
- **Diarisation** : « qui parle quand » (Pyannote).
- **OKF** : Open Knowledge Format (Google, 2026) — .md + YAML frontmatter pour agents.
- **MCP** : Model Context Protocol — accès des agents aux outils/données.
- **Hermes Agent** : agent autonome persistant auto-hébergé (Nous Research).
- **Pi (pi.dev)** : harnais d'agent de code minimal (Mario Zechner) ; base d'OpenClaw.
- **Matter / Thread / Zigbee** : protocoles domotiques (côté serveur HA).
- **Thread Border Router** : passerelle du réseau maillé Thread.

---

## 16. Sources / références

- Home Assistant — doc Assist, protocole Wyoming, intégration Ollama, Matter.
- Seeed Studio Wiki + FormatBCE (GitHub) — intégration ESPHome du XVF3800.
- Guides 2026 « fully local voice assistant » (faster-whisper + Piper + Ollama).
- Google Cloud — annonce & spec **OKF** (12 juin 2026, GitHub Knowledge Catalog).
- Nous Research — **Hermes Agent** (doc, profils git). **pi.dev** — Pi coding agent.
- xda-developers / community HA — satellites ESP32-S3, ESP32-S3-BOX-3.

> *Synthèse d'architecture, pas une procédure pas-à-pas. Chaque phase (§11) pourra
> devenir une fiche dédiée dans le vault.*

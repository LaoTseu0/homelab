# Paysage des outils — la pile et ses alternatives

> Repère visuel : chaque couche de l'architecture, l'outil en place (ou
> pressenti), et les alternatives connues — pour élargir le champ de vision
> avant chaque décision, pas pour tout tester.
> Complète [../architecture/jarvis.md](../architecture/jarvis.md) et
> [../architecture/inference.md](../architecture/inference.md).
> Dernière mise à jour : 18 juillet 2026
> Statut : exploration, vivant — enrichir au fil de la veille

Légende : ✅ en place · 🧭 pressenti, non tranché · 💤 connu, non exploré
· ❌ écarté (raison donnée)

---

## 1. La pyramide — vue d'ensemble

Du matériel (bas) vers l'humain (haut). Chaque étage est détaillé dans une
section ci-dessous, avec ses alternatives.

```
                                ▲ proche de l'humain
                 ┌──────────────────────────────┐
            §8   │   INTERACTION                │  satellites vocaux,
                 │   XVF3800 ✅ · Open WebUI 🧭 │  interfaces de chat
               ┌─┴──────────────────────────────┴─┐
          §7   │   AGENTS & MÉMOIRE               │  Hermes/Pi 🧭,
               │   couche agentique · OKF 🧭      │  mémoire persistante
             ┌─┴──────────────────────────────────┴─┐
        §6   │   ORCHESTRATION & RAG                │  la glu : routage,
             │   maison 🧭 · Qdrant 🧭 · BGE-M3 🧭  │  retrieval, evals
           ┌─┴──────────────────────────────────────┴─┐
      §5   │   VOIX & DOMOTIQUE                       │  Home Assistant ✅
           │   HA ✅ · Wyoming ✅ · Whisper/Piper ✅   │  wake/STT/TTS
         ┌─┴──────────────────────────────────────────┴─┐
    §4   │   SERVEUR D'INFÉRENCE                        │  qui sert le
         │   Ollama ✅ (voix) · llama.cpp/vLLM 🧭 (core)│  modèle
       ┌─┴──────────────────────────────────────────────┴─┐
  §3   │   MODÈLES                                        │  ce qui pense :
       │   Qwen3 4B ✅ (voix) · Qwen3.6-27B 🧭 (core)     │  LLM, embeddings
     ┌─┴──────────────────────────────────────────────────┴─┐
§2   │   SOCLE                                              │  OS, conteneurs,
     │   Ubuntu Server ✅ · Docker ✅ · NVIDIA Toolkit ✅    │  accès GPU
     └────────────────────────────────────────────────────────┘
                                ▼ proche du matériel
```

---

## 2. Socle — OS, conteneurs, GPU

| Choix | Statut | Où |
|---|---|---|
| Ubuntu Server + Docker + NVIDIA Container Toolkit | ✅ jarvis-central | [installation.md](../serveurs/jarvis-central/installation.md) |
| OS de jarvis-core | 🧭 à trancher | [inference.md §6](../architecture/inference.md) |

| Alternative | Nature | Quand y penser |
|---|---|---|
| Debian | même famille, plus minimal, cycle plus lent | si l'envie d'un socle encore plus stable/sobre |
| Proxmox VE | hyperviseur : VMs + LXC | si besoin de plusieurs OS isolés sur une machine (HAOS en VM + Linux à côté) |
| Home Assistant OS | appliance tout-en-un, add-ons clic-bouton | ❌ écarté : moins aligné « une brique à la fois » (choix documenté, installation.md) |
| NixOS | config déclarative, reproductible | séduisant pour du config-as-code intégral ; courbe d'apprentissage réelle |
| Podman | conteneurs sans démon, rootless | si la surface du démon Docker devient une gêne (sécurité) |
| k3s / Kubernetes | orchestrateur de conteneurs | surdimensionné à cette échelle ; utile côté employabilité ([formation](../formation/roadmap.md)) |

## 3. Modèles

| Choix | Statut |
|---|---|
| Qwen3 4B Instruct (voix, tool calling) | ✅ jarvis-central |
| Qwen3.6-27B / Qwen3-Coder 30B-A3B / Gemma 4 12B QAT / gpt-oss 120B | 🧭 candidats jarvis-core — voir [inference.md §4](../architecture/inference.md) |

| Alternative | Nature | Quand y penser |
|---|---|---|
| Llama (Meta) | famille ouverte historique | 💤 le 70B dense est dépassé par les ~27-30B récents à VRAM égale ([inference-locale.md §1](inference-locale.md)) |
| Mistral / Magistral | famille européenne, bons petits modèles | si un modèle FR-first devient un critère |
| DeepSeek (distills) | raisonneurs distillés en petites tailles | pour tester du « thinking » local — ⚠️ think-mode inutilisable en voix |
| Phi (Microsoft) | petits modèles denses très optimisés | alternative au 4B pour la voix si Qwen déçoit |
| GLM / frontier via API | le haut du panier, payant, données sortantes | fallback assumé pour tâches lourdes — contredit le 100 % local, à doser |

## 4. Serveur d'inférence

| Choix | Statut |
|---|---|
| Ollama | ✅ jarvis-central (voix) — intégration HA native |
| llama.cpp / Ollama / vLLM | 🧭 à trancher pour jarvis-core ([inference.md §6](../architecture/inference.md)) |

| Alternative | Nature | Quand y penser |
|---|---|---|
| llama.cpp (serveur) | le moteur sous Ollama, contrôle fin | **requis** si offload MoE (gpt-oss 120B) : flag `--n-cpu-moe` |
| vLLM | serveur de prod GPU : batching continu, PagedAttention | plusieurs clients simultanés ; benchmark prévu (formation, module 4) |
| ExLlamaV2 / TabbyAPI | inférence VRAM-only très rapide (format EXL2) | si tout tient en VRAM et que chaque tok/s compte |
| LM Studio | GUI desktop, découverte de modèles | onboarding non-tech ; pas pour un serveur headless |
| koboldcpp | fork llama.cpp orienté narration/roleplay | 💤 hors besoin |
| TGI (Hugging Face) / SGLang | serveurs de prod alternatifs | 💤 culture générale infra ; vLLM couvre le besoin |

## 5. Voix & domotique

### Le chef d'orchestre

| Choix | Statut |
|---|---|
| Home Assistant | ✅ — Assist, intégration Ollama, écosystème Wyoming |

| Alternative | Nature | Quand y penser |
|---|---|---|
| Jeedom | domotique FR, plugins payants | 💤 communauté FR forte, mais écosystème voix/LLM très en retrait de HA |
| Gladys Assistant | domotique FR open source, dev actif | 💤 sympathique, écosystème bien plus petit |
| openHAB | équivalent Java de HA | 💤 aucun avantage ici |
| Domoticz / ioBroker | vétérans légers | 💤 idem |
| Node-RED | flux visuels, s'ajoute à HA | **complément**, pas remplaçant — automatisations complexes |

### Le pipeline vocal (briques Wyoming)

```
[ wake word ] ──► [ STT ] ──► intents HA / LLM ──► [ TTS ]
 openWakeWord ✅   faster-whisper ✅                 Piper ✅
```

| Brique | Alternatives | Quand y penser |
|---|---|---|
| Wake word — openWakeWord ✅ | **micro_wake_word** (détection sur la puce ESP32-S3) | dès les satellites ESP32 — décharge le serveur |
| | Porcupine (Picovoice) | précis mais propriétaire, licence limitée — ❌ hors philosophie |
| | wake word custom « ok jarvis » | déjà au [backlog](../backlog.md) (entraînement openWakeWord) |
| STT — faster-whisper ✅ | whisper.cpp | même famille en C++ (Vulkan/CPU) — si un jour hors CUDA |
| | Vosk | léger, streaming temps réel, moins précis — satellites très contraints |
| | Speech-to-Phrase | vocabulaire fermé quasi instantané — STT **sur un Pi** |
| | NVIDIA Parakeet / Canary | très rapides sur GPU — à surveiller pour le français |
| TTS — Piper ✅ | Kokoro | qualité nettement supérieure, encore léger — **le premier à tester** si la voix siwis lasse |
| | Coqui XTTS | clonage de voix multilingue — projet en sommeil, lourd |
| | MeloTTS / OpenVoice | alternatives crédibles, FR à vérifier |
| | espeak-ng | robotique — dépannage uniquement |
| Protocole — Wyoming ✅ | intégrations HA natives (cloud) | ❌ contredit le 100 % local |
| | pipeline maison (WebSocket/MQTT) | seulement si le [routeur multi-modèles](../architecture/router-multi-model.md) l'exige un jour |

### Protocoles domotique (côté serveur HA)

| Choix pressenti | Alternatives | Quand y penser |
|---|---|---|
| Zigbee 🧭 (le plus mûr — [jarvis.md §8](../architecture/jarvis.md)) | ZHA (intégré HA) **ou** Zigbee2MQTT | à trancher à l'achat du coordinateur : ZHA simple, Z2M plus riche/portable |
| | Matter / Thread | l'avenir, encore « early adopter » — ajouter au fil de l'eau |
| | Z-Wave | mûr aussi, matériel plus cher, moins de choix |
| | WiFi DIY : ESPHome / Tasmota | capteurs maison sur ESP32 — ESPHome s'impose (même écosystème que les satellites) |

## 6. Orchestration & RAG

| Choix | Statut |
|---|---|
| Orchestrateur maison (« les 15 lignes ») | 🧭 — [inference-locale.md §6](inference-locale.md) |
| Qdrant + BGE-M3 + reranker bge-v2-m3 | 🧭 — même source |

| Brique | Alternatives | Quand y penser |
|---|---|---|
| Framework — maison 🧭 | LlamaIndex | centré RAG — prévu en v3 du module 2 ([formation](../formation/roadmap.md)) pour parler le vocabulaire du marché |
| | LangChain / LangGraph | chaînes et graphes — omniprésents dans les offres, à connaître plus qu'à adopter |
| | Haystack / Pydantic AI / DSPy | alternatives citées en entretien — 💤 culture |
| Base vectorielle — Qdrant 🧭 | Chroma | embarqué, zéro service — prototypage |
| | FAISS | bibliothèque (pas un serveur) — dans un script, pas dans l'archi |
| | pgvector | si un Postgres existe déjà — un service en moins |
| | LanceDB / Milvus / Weaviate | 💤 savoir situer |
| Embeddings — BGE-M3 🧭 | nomic-embed-text (via Ollama) | zéro service en plus — bon candidat v1 du module 2 |
| | E5 / GTE / Jina | à comparer **avant** d'indexer : changer = tout ré-indexer ([décision verrouillante](inference-locale.md)) |
| Reranker — bge-reranker-v2-m3 🧭 | cross-encoders ms-marco (MiniLM) | plus légers, moins bons en FR |
| | ColBERT | late interaction, autre paradigme — 💤 R&D |
| UI de chat — Open WebUI 🧭 | LibreChat | multi-providers, multi-utilisateurs |
| | Lobe Chat / text-generation-webui | 💤 alternatives connues |

## 7. Agents & mémoire

| Choix | Statut |
|---|---|
| Hermes Agent **ou** Pi | 🧭 — question ouverte n°2 de [jarvis.md §14](../architecture/jarvis.md) |
| Mémoire OKF (.md + git + Obsidian) | 🧭 — [jarvis.md §6](../architecture/jarvis.md) |

| Brique | Alternatives | Quand y penser |
|---|---|---|
| Harnais — Hermes 🧭 / Pi 🧭 | OpenClaw | ❌ ≈138 CVE début 2026 — leçon de sécurité, pas un outil |
| | Claude Code / Codex CLI | excellents mais cloud — contredit le 100 % local pour Jarvis ; restent des outils de dev |
| | Aider / OpenHands / goose | agents de code open source — si Hermes et Pi déçoivent |
| | boucle maison (~200 lignes) | prévue au module 1 ([formation](../formation/roadmap.md)) — comprendre avant d'adopter |
| Mémoire — OKF 🧭 | mem0 / Zep / Letta (MemGPT) | mémoire « produit » (API, scoring) — ❌ tant que markdown+git suffit : lisible, versionné, sans service |
| | mémoire vectorielle pure | se combine (RAG sur la mémoire) plutôt qu'elle ne remplace |
| Protocole outils — MCP 🧭 | function calling natif (OpenAI-compatible) | suffit tant qu'il n'y a qu'un client et un serveur |
| | ⚠️ coût en contexte de MCP | vécu : le rejet de MCP par Pi — à évaluer par outil |

## 8. Interaction

| Brique | Choix | Alternatives | Quand y penser |
|---|---|---|---|
| Satellite exigeant (salon) | XVF3800 ✅ (USB) | — | far-field 4 micros, AEC matériel |
| Satellites secondaires | ESP32-S3 🧭 | ESP32-S3-BOX-3 (clé en main) | pièces secondaires, petit budget |
| | | Pi 5 + micro USB | si un écran/du calcul local au satellite |
| | | ⚠️ ESP32-C6/H2 | seulement pour Thread/Matter (radio 802.15.4), pas pour la voix |
| Interface texte | chat Assist (HA) ✅ | Open WebUI 🧭 (§6) | dès que jarvis-core sert un modèle |

## 9. Transverse — observabilité & evals (formation, modules 2 et 6)

| Brique | Choix | Alternatives | Quand y penser |
|---|---|---|---|
| Traces LLM | Langfuse 🧭 (self-hostable) | LangSmith / Helicone / Arize Phoenix | SaaS ou cloud-first — ❌ données sortantes |
| Evals RAG | script maison d'abord 🧭 | RAGAS / DeepEval / promptfoo | en fin de module 2, pour connaître l'outillage standard |

---

## Comment se servir de ce document

- **Avant chaque décision** : relire la section de la couche concernée —
  l'alternative écartée hier peut avoir mûri.
- **Au fil de la veille** ([jarvis.md §10](../architecture/jarvis.md)) : ajouter
  les nouveaux venus ici, avec leur ligne « quand y penser » — une ligne
  suffit, ce n'est pas un comparatif.
- **Quand une couche est tranchée** : le choix remonte dans
  `architecture/`, ce document garde la liste des alternatives (c'est sa
  valeur : le jour où le choix déçoit, le plan B est déjà repéré).

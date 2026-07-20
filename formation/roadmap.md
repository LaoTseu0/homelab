# Roadmap AI Engineer — socle technique d'apprentissage

> **Rôle de ce document** : feuille de route de formation pour maîtriser la
> stack LLM complète (inférence, orchestration, agents, production), avec un
> double objectif : être capable de **produire chaque couche soi-même**, et
> être **opérationnel et demandé sur le marché du travail** (profil
> AI Engineer). Le homelab (Jarvis) sert de terrain d'entraînement et de
> portfolio — voir [architecture/jarvis.md](../architecture/jarvis.md).
> Couvre l'intégralité des sujets de la roadmap de référence
> [roadmap.sh/ai-engineer](https://roadmap.sh/ai-engineer) (correspondance en §9)
> et confrontée aux offres d'emploi réelles (relevé de terrain en §10).
> **Dernière mise à jour** : 11 juillet 2026
> **Statut** : vivant — cocher les acquis, enrichir au fil de la veille

---

## 1. Principe directeur

Même logique que le homelab : **incrémental, DIY, chaque brique comprise
avant d'empiler la suivante**.

1. **Refaire à la main d'abord, adopter le framework ensuite.** On ne
   comprend ce que LangChain automatise qu'après avoir écrit la version
   en Python pur. En entretien, c'est ce qui distingue des candidats qui
   n'ont jamais regardé sous le capot.
2. **Chaque module produit un livrable qui tourne** — idéalement utile au
   homelab, toujours versionné, avec un README en anglais. Un recruteur
   croit un repo qui tourne, pas une certification.
3. **Mesurer, toujours.** Un projet LLM sans évaluation chiffrée est une
   démo, pas de l'ingénierie. Les evals sont LE différenciateur (§2, couche T).

---

## 2. La stack complète — carte des couches

```
Couche T  PRODUCTION (transverse) : evals, observabilité, sécurité, coûts
Couche 4  PROTOCOLES : API OpenAI-compatible, MCP, function calling
Couche 3  AGENTS : boucle outils, harnais (Pi, Claude Code), sandboxing
Couche 2  ORCHESTRATION : RAG, embeddings, bases vectorielles,
          LangChain / LlamaIndex, pipelines, structured outputs
Couche M  MULTIMODAL (transverse) : vision, audio, STT/TTS, images
Couche 1  INFÉRENCE : vLLM, llama.cpp, Ollama, quantization, GPU,
          paysage des modèles (ouverts / fermés)
Couche 0  FONDAMENTAUX : tokens, attention, contexte, sampling,
          prompt & context engineering
```

### Couche 0 — Fondamentaux (comprendre, pas produire)

Ce qu'un AI Engineer doit savoir *expliquer* (pas re-dériver les maths) :

**Vocabulaire de base** (les définitions qu'on doit pouvoir donner sans
hésiter en entretien) :

- **IA vs AGI** ; **LLM** ; **inférence vs entraînement** (l'AI Engineer
  vit côté inférence — l'entraînement est le métier du ML Engineer) ;
- **Tokenisation** : le modèle ne voit pas des mots. Conséquences
  pratiques : coûts, limites, pourquoi le comptage de lettres échoue.
- **Attention / transformer** : intuition du mécanisme, pourquoi le
  contexte coûte quadratiquement, ce qu'est le **KV cache**.
- **Fenêtre de contexte** : ce qui s'y passe (prompt système + historique
  + outils + documents), pourquoi elle déborde — vécu concret : le rejet
  de MCP par Pi pour son coût en contexte.
- **Embeddings** : projeter du texte dans un espace vectoriel où « proche »
  = « sémantiquement similaire ». Le socle du RAG (couche 2).
- **Quantization** : q4_K_M et compagnie — troquer de la précision contre
  de la VRAM. Déjà pratiqué (Qwen3 4B sur la RTX 2060).

**Paramètres de sampling** (à savoir régler ET expliquer) :

- **temperature** — aléa de la génération ; ce que « déterministe » veut
  dire (et ne veut pas dire) ;
- **top-k / top-p** — restreindre le vocabulaire candidat ;
- **repetition penalties** — éviter les boucles.

**Prompt engineering** (les techniques nommées, car les offres et les
entretiens utilisent ces termes) :

- **zero-shot** (consigne seule) / **few-shot** (avec exemples) ;
- **chain-of-thought (CoT)** — faire raisonner étape par étape ;
- **ReAct** — alterner raisonnement et action (le pattern derrière
  toutes les boucles d'agent, couche 3) ;
- prompt système, rôle & comportement, contraintes d'entrée/sortie,
  format d'entrée.

**Context engineering** (le terme qui a supplanté « prompt engineering »
dans les offres — gérer *tout* ce qui entre dans la fenêtre) :

- **structured outputs** et **function calling** (détaillés couches 2 et 3) ;
- **prompt caching** — ne pas re-payer le préfixe stable à chaque appel ;
- **streaming** des réponses (l'UX de tout chat) ;
- **compaction de contexte** (résumer l'historique), **isolation de
  contexte** (cloisonner les sous-tâches), **mémoire externe** (déporter
  le long terme dans des fichiers/DB — exactement la mémoire OKF de
  Jarvis), **RAG et filtres dynamiques** (n'injecter que le pertinent).

📚 Références : 3Blue1Brown (série transformers), Karpathy (« Let's build
GPT », « Intro to LLMs »), le playground de tokenizer d'OpenAI/HF.

### Couche 1 — Inférence : faire tourner le modèle

| Outil | Nature | À maîtriser pour |
|---|---|---|
| **llama.cpp** | moteur C++, GGUF, CPU-friendly | comprendre la quantization, le local léger |
| **Ollama** | surcouche conviviale de llama.cpp | déjà acquis (homelab) — API REST, gestion modèles |
| **LM Studio** | équivalent desktop d'Ollama avec GUI | savoir que ça existe (onboarding non-tech) |
| **vLLM** | serveur de production GPU (batching continu, PagedAttention) | les offres « LLM infra » ; servir un modèle à N utilisateurs |
| **HF Transformers** | bibliothèque Python de référence | charger/inspecter un modèle à la main, comprendre ce que les serveurs enrobent |

Notions clés : débit (tokens/s) vs latence, batching, KV cache, VRAM
(poids + cache + contexte), choix CPU/GPU.

**Le paysage des modèles** (savoir s'orienter et justifier un choix) :

- **Fermés (API)** : Anthropic Claude, OpenAI (GPT / o-series), Google
  Gemini — l'état de l'art, payant au token, données qui sortent.
- **Ouverts (poids téléchargeables)** : Qwen, Gemma, Llama, Mistral,
  DeepSeek — self-hostables (déjà pratiqué), niveaux variés.
- **Pré-entraîné vs fine-tuné vs self-hosted** : les trois régimes
  d'utilisation ; le fine-tuning est rarement la bonne réponse (voir
  couche T, LoRA).
- **Hugging Face** : le hub central (modèles, datasets, spaces), son
  Inference SDK, Transformers.js pour le navigateur.
- **OpenRouter** : agrégateur multi-providers derrière une seule API —
  utile pour comparer des modèles sans multiplier les comptes.
- **Choisir le bon modèle** : coût / latence / qualité / confidentialité /
  taille de contexte — le raisonnement du
  [routeur multi-modèles](../architecture/router-multi-model.md) appliqué
  au métier. Question d'entretien classique.

### Couche 2 — Orchestration : câbler le LLM dans une application

**C'est là que sont la majorité des postes.** Le cœur du métier AI Engineer :

**Embeddings et bases vectorielles** :

- cas d'usage au-delà du RAG : **recherche sémantique**, **classification**,
  **recommandation**, **détection d'anomalies** ;
- modèles d'embeddings : ouverts (**sentence-transformers**, Jina, modèles
  HF, `nomic-embed-text` via Ollama) et API (OpenAI, Cohere, Gemini) ;
- bases vectorielles — le marché dit « pick one », en connaître une à
  fond et situer les autres : **Qdrant** (self-hostable, choix homelab),
  Chroma (léger, embarqué), FAISS (bibliothèque, pas un serveur),
  pgvector/Supabase (Postgres), Pinecone (SaaS), Weaviate, LanceDB,
  MongoDB Atlas ;
- mécanique interne : indexation (HNSW…), recherche par similarité
  (cosinus), compromis rappel/vitesse.

**RAG** (Retrieval-Augmented Generation) :

- la chaîne complète : **chunking → embedding → stockage → retrieval →
  génération** avec citations des sources ;
- retrieval hybride (BM25 + vecteurs), re-ranking ;
- **RAG vs fine-tuning** : question d'entretien récurrente — le RAG pour
  la connaissance changeante/sourçable, le fine-tuning pour le style et
  les formats, presque jamais pour injecter des faits ;
- les façons de l'implémenter, par ordre pédagogique : **SDK direct**
  (à la main — module 2 v1), puis **LlamaIndex** (centré RAG) ou
  **LangChain/LangGraph** (chaînes et graphes) ; situer Haystack et
  RAGFlow (alternatives que citent certaines offres).

**Structured outputs** : forcer du JSON valide (JSON mode, schémas,
Pydantic), valider, réessayer. Indispensable dès qu'un LLM alimente du code.

**Pipelines batch** : traitement en masse (classification, extraction,
tagging) avec reprise sur erreur et validation des sorties.

### Couche M — Multimodal (transverse) : au-delà du texte

Le domaine où le homelab a une longueur d'avance : **le pipeline vocal de
Jarvis est déjà du multimodal en production** (Whisper = speech-to-text,
Piper = text-to-speech). À savoir raconter en ces termes.

- **Tâches** : compréhension d'image (VLM), génération d'images,
  compréhension vidéo, traitement audio, **STT** ✅ (Whisper — acquis),
  **TTS** ✅ (Piper — acquis) ;
- **Implémentation locale** : modèles vision-language via Ollama
  (Qwen-VL, LLaVA…), Whisper (acquis), modèles HF ;
- **Implémentation API** (à connaître de nom pour les offres) : vision
  GPT/Claude/Gemini, génération d'images (DALL-E, Nano Banana),
  Whisper API ; support multimodal de LangChain/LlamaIndex ;
- Débouché homelab naturel : caméra + VLM local → « Jarvis, qu'est-ce
  qu'on voit dans le jardin ? » (module 7).

### Couche 3 — Agents : le LLM qui agit

- **La boucle d'agent** : réfléchir → appeler un outil → lire le résultat
  → recommencer (= **ReAct** industrialisé). À écrire soi-même une fois
  (pattern Pi : 4 outils, une boucle while — « manual implementation »
  dans les référentiels).
- **Function calling / tool use** : définir des outils (schémas JSON),
  parser les appels, exécuter, renvoyer.
- **Les SDKs d'agents** (à situer, l'un à pratiquer) : **Claude Agent
  SDK**, **OpenAI Agents SDK / AgentKit**, Google **ADK** / Vertex AI
  Agent Builder. Même boucle que la version manuelle, en produit.
- **Multi-agents** : orchestrer plusieurs agents (superviseur/ouvriers,
  pipelines) — à comprendre, et à aborder avec le scepticisme de Pi
  (des sessions séparées observables battent souvent la boîte noire).
- **Harnais existants** : Pi, Claude Code, Hermes — savoir les utiliser
  est un prérequis générique ; savoir les **étendre** (extensions, hooks,
  skills) et les **confiner** est une compétence.
- **Sandboxing et garde-fous** : moindre privilège, interception des
  appels d'outils (hook `tool_call` de Pi), conteneurs, validation
  humaine des actions destructives. Voir
  [architecture/securite.md](../architecture/securite.md) §5 — les
  non-négociables du homelab sont exactement les bonnes pratiques métier.

### Couche 4 — Protocoles : la glu

- **API OpenAI-compatible** : le standard de fait pour parler à un moteur
  d'inférence (Ollama, vLLM, llama.cpp l'exposent tous) — c'est elle qui
  rend les couches interchangeables. Connaître aussi les API natives
  (Claude Messages API, OpenAI Responses API, Gemini API) : structures
  de messages, rôles, tool calls.
- **MCP** (Model Context Protocol) — l'architecture complète, pas juste
  le mot-clé :
  - les rôles : **host** (l'app IA), **client** (la connexion), **serveur**
    (l'exposeur d'outils/ressources/prompts) ;
  - les couches : **données** (JSON-RPC 2.0, découverte `tools/list` /
    `tools/call`) et **transport** (stdio en local, HTTP en distant) ;
  - savoir **écrire un serveur** (module 5) *et* **un client**, connecter
    local et distant.
- **Skills** (standard Agent Skills) : `SKILL.md` + frontmatter, divulgation
  progressive — le format portable pour donner du savoir-faire à un agent.

### Couche T — Production (transverse, ce qui fait le senior)

**Évaluations** — le différenciateur n°1 en entretien :

- les trois familles : **déterministes** (exact match, regex, schéma
  valide — rapides, fiables), **model-based / LLM-as-judge** (un modèle
  note les réponses — souple, à calibrer), **humaines** (référence,
  coûteuses) ;
- **métriques** : exactitude, fidélité aux sources (RAG), pertinence du
  retrieval, taux de refus/hallucination ;
- **tests de non-régression** : un jeu de cas figé, un score avant/après
  chaque changement de prompt/modèle/chunking — traiter les prompts
  comme du code ;
- outils : **RAGAS** (RAG), **DeepEval**, promptfoo — ou script maison
  assumé (module 2).

**Observabilité** :

- tracer chaque appel : prompt, réponse, latence, tokens, **coût** ;
  monitoring de production (dérive, erreurs) ;
- outils : **Langfuse** (self-hostable ✅ — choix homelab), LangSmith,
  Helicone, Arize.

**Sécurité et éthique** :

- **prompt injection** (directe et indirecte — le cas d'école : une
  instruction malveillante dans un document indexé par le RAG),
  exfiltration par outil, **OWASP Top 10 for LLM Applications** — à
  connaître par cœur ;
- **tests adversariaux** : attaquer soi-même son système avant les autres ;
- **biais et équité**, modération de contenu (APIs dédiées), contraindre
  entrées ET sorties, connaître ses utilisateurs/usages (KYC), IDs
  utilisateur dans les appels API (traçabilité des abus) ;
- confidentialité : quelles données partent vers quelles API — l'ADN
  local-first du homelab est un argument d'entretien.

**Coûts et dimensionnement** : estimer tokens/mois, local vs API, petit
vs gros modèle par tâche (le
[routeur multi-modèles](../architecture/router-multi-model.md) est ce
raisonnement appliqué).

**Fine-tuning (culture)** : LoRA/QLoRA sur petit modèle — savoir ce que
c'est, ce que ça coûte, et pourquoi RAG ou prompt suffisent 9 fois sur 10.

---

## 3. Le marché — où sont les postes, comment ils s'appellent

| Intitulé | Cœur du poste | Couches | Volume d'offres |
|---|---|---|---|
| **AI Engineer / LLM Engineer** | brancher des LLM sur les données et process d'une entreprise : RAG, agents, evals, mise en prod | 2, 3, 4, T | ⭐⭐⭐ le gros du marché |
| **LLM Infra / MLOps GPU** | servir des modèles : vLLM, GPU, K8s, monitoring, coûts | 1, T | ⭐⭐ moins d'offres, moins de candidats |
| **ML Engineer / Data Scientist LLM** | fine-tuning, entraînement, données | 0-1 + maths | ⭐ marché plus petit, plus exigeant |
| **Forward Deployed Engineer** | AI Engineer déployé chez le client : intégration + conseil | 2-4, T + relationnel | ⭐ en croissance (profil senior) |
| **Développeur « augmenté »** | dev classique + maîtrise des outils IA | 3 (usage) | prérequis générique, pas un métier |

> **AI Engineer vs ML Engineer** — la distinction canonique : l'AI Engineer
> **utilise** des modèles pré-entraînés via API/inférence pour construire
> des produits ; le ML Engineer **entraîne** des modèles. Pas les mêmes
> outils, pas les mêmes maths, pas le même marché.

**Mots-clés qui reviennent dans les offres AI Engineer (2026)** : RAG,
embeddings, vector database, LangChain/LlamaIndex, function calling,
agents, MCP, evals, context engineering, FastAPI, Python, Docker.
Côté infra : vLLM, quantization, CUDA (notions), Kubernetes, Terraform.

**Ce qui trie les candidats en entretien** (dans l'ordre) :

1. « Comment évaluez-vous votre système ? » — 90 % n'ont pas de réponse.
2. « Expliquez ce qui se passe quand le modèle appelle un outil » — au
   niveau HTTP/JSON, pas au niveau « le framework s'en occupe ».
3. « Votre RAG répond mal : comment diagnostiquez-vous ? » (retrieval ?
   chunking ? prompt ? modèle ? — démarche de debug par couche).
4. « RAG ou fine-tuning pour ce besoin ? » (et pourquoi).
5. « Quels risques de sécurité pour un agent avec accès fichiers ? »
6. Un repo GitHub qui tourne, documenté, avec des métriques.

**Atouts déjà en main** (à assumer dans un CV) : self-hosting complet,
Docker, GPU/quantization en pratique, **pipeline multimodal en production**
(STT/TTS), architecture réseau et sécurité raisonnées, documentation de
qualité professionnelle — le repo homelab en est la preuve.

---

## 4. Compétences transverses — les prérequis

- **Python d'abord** : tout l'écosystème couche 2/T est en Python.
  Niveau visé : à l'aise avec venv/uv, typing, Pydantic, `httpx`/`requests`,
  async de base, tests pytest. **FastAPI** pour exposer ses services
  (le standard des micro-services IA).
- **Base web full-stack** : le prérequis d'entrée des référentiels
  AI Engineer (frontend *ou* backend *ou* full-stack). Le backend est
  le versant qui compte ici : API, HTTP, JSON, bases de données.
- **TypeScript en second** : les harnais (Pi, SDKs Anthropic/OpenAI)
  et le front. Utile, pas prioritaire.
- **Outils de dev assistés par IA** — en 2026 c'est un attendu, plus un
  bonus : pratiquer sérieusement **Claude Code** (fait — ce repo),
  situer Codex, Cursor, Windsurf, Gemini CLI, Replit. En entretien,
  savoir décrire *son* workflow avec ces outils.
- **Git avancé** : déjà acquis (serveur bare, workflow doc) — savoir le
  raconter.
- **Docker** : déjà acquis — ajouter docker compose multi-services avec
  réseau interne (fait) et, à terme, des notions Kubernetes (beaucoup
  d'offres infra le demandent, inutile pour commencer).
- **Anglais écrit** : READMEs, posts, veille. Le portfolio public doit
  être en anglais.

---

## 5. Le parcours — modules et projets adossés au homelab

> Chaque module : un objectif, un livrable versionné, et la ligne qu'il
> ajoute au CV. Ordre conçu pour que chaque étage explique le suivant.
> Les durées supposent un rythme soirées/week-ends.

### Module 1 — Le socle sans framework *(2-3 semaines)*

Écrire en **Python pur** contre l'Ollama du homelab
(`http://192.168.1.57:11434`, voir [architecture/reseau.md](../architecture/reseau.md) —
endpoint amené à changer : restriction à `127.0.0.1` prévue côté sécurité,
et l'inférence lourde déménage sur `jarvis-core`, voir
[architecture/inference.md](../architecture/inference.md)) :

- [x] un chat en CLI avec historique de conversation (gestion du contexte
      à la main : troncature, résumé/compaction) — avec **streaming** ;
- [x] expérimenter les **paramètres de sampling** (temperature, top-k,
      top-p) et les techniques de prompt (zero/few-shot, CoT) sur des cas
      concrets, noter les effets ;
- [x] du **function calling à la main** : définir 2-3 outils en schéma
      JSON, parser la sortie du modèle, exécuter, renvoyer le résultat
      (= comprendre **ReAct** en l'implémentant) ;
- [x] une **mini-boucle d'agent** (pattern Pi) : read/write/edit/bash
      dans une boucle while, ~200 lignes ;
- [x] du **structured output** : extraction d'infos en JSON validé
      Pydantic, avec retry en cas de JSON invalide.

**✅ Module 1 terminé le 20 juillet 2026** — livrable : `formation/llm-from-scratch`
(8 scripts + README anglais + PROGRESSION.md) ; extraction en repo dédié
reportée, à décider par Anthony.

**Livrable** : repo `llm-from-scratch` (ou équivalent), README anglais
expliquant chaque mécanisme.
**CV** : « implemented tool-calling agent loop from scratch against a
self-hosted LLM ».

### Module 2 — RAG complet : interroger la doc du homelab *(1 mois)*

Le projet : « qu'est-ce qu'on avait décidé pour le backup du NAS ? » →
réponse sourcée depuis les `.md` de ce repo.

- [ ] **v1 à la main** : chunking des `.md`, embeddings via Ollama
      (`nomic-embed-text` ou équivalent), stockage SQLite + similarité
      cosinus maison, top-k dans le prompt, citations des fichiers sources ;
- [ ] **v2 outillée** : migrer vers **Qdrant** (conteneur — un service de
      plus dans le style du homelab) ; ajouter le retrieval hybride
      (BM25 + vecteurs) et comparer ;
- [ ] **v3 framework** : refaire en **LlamaIndex** pour parler le
      vocabulaire du marché — et documenter ce que le framework a
      apporté / caché ;
- [ ] **Evals dès la v1** : 30 questions/réponses attendues, score
      automatisé (déterministe + LLM-as-judge), tableau de non-régression
      v1 → v2 → v3 ; passer le jeu dans **RAGAS** ou **DeepEval** en fin
      de module pour connaître l'outillage standard. *C'est la partie la
      plus valorisable du module.*
- [ ] savoir conclure : **RAG vs fine-tuning**, pourquoi RAG était le bon
      choix ici (réponse d'entretien rédigée dans le README).

**Livrable** : repo `homelab-rag` avec le tableau de métriques dans le
README.
**CV** : « built and evaluated a RAG pipeline end-to-end (custom, then
Qdrant + LlamaIndex), with regression evals ».

### Module 3 — L'agent maison : « Hermes sur base Pi » *(1-2 mois, = Phase 3 Jarvis)*

Fusion formation × roadmap Jarvis (voir
[architecture/jarvis.md](../architecture/jarvis.md) §7) :

- [ ] extension Pi **hook `tool_call`** : liste noire de commandes
      destructives + validation humaine — le non-négociable de
      [architecture/securite.md](../architecture/securite.md) §5 ;
- [ ] **outil custom `home_assistant`** (`pi.registerTool`) appelant
      l'API REST de HA avec un token à périmètre limité ;
- [ ] **mémoire versionnée** : hooks `session_start`/`session_shutdown`
      → git pull/commit sur le dépôt mémoire (convention OKF) —
      c'est le pattern « external memory » du context engineering ;
- [ ] **conteneur dédié** à l'agent, moindre privilège, aucun accès aux
      partages famille ;
- [ ] (bonus) mode **RPC/SDK** : un petit service qui tient une session
      Pi ouverte — l'embryon d'agent persistant ;
- [ ] (bonus culture) refaire un mini-agent avec un **SDK du marché**
      (Claude Agent SDK ou OpenAI Agents SDK) pour comparer avec la
      version manuelle et le harnais — trois régimes, même boucle.

**Livrable** : repo `jarvis-agent` (le `.pi/` complet versionné = le
« profil » de l'agent) + note de conception dans `architecture/`.
**CV** : « designed a sandboxed autonomous agent with tool-call
interception, human-in-the-loop guardrails and git-versioned memory ».
*Le projet portfolio le plus original du lot — personne d'autre n'a ça.*

### Module 4 — Infra : vLLM et le métier de servir *(2 semaines, en parallèle)*

- [ ] déployer **vLLM** en conteneur sur la RTX 2060 avec un petit modèle ;
- [ ] **benchmark documenté** vs Ollama : tokens/s, latence premier token,
      comportement à 1 / 5 / 20 requêtes concurrentes (script de charge
      maison) ;
- [ ] comprendre et expliquer les résultats : batching continu, KV cache,
      PagedAttention ;
- [ ] rédiger le verdict : quand Ollama suffit, quand vLLM se justifie.

**Livrable** : post de blog / README `ollama-vs-vllm-bench` avec les
chiffres.
**CV** : « deployed and benchmarked vLLM vs Ollama on consumer GPU ».

### Module 5 — MCP : un serveur ET un client *(1-2 semaines, gros rendement)*

- [ ] écrire un **serveur MCP en Python** exposant le homelab en
      lecture : état des conteneurs, entités HA, recherche dans la doc
      (réutilise le module 2 !) — transport stdio d'abord, HTTP ensuite ;
- [ ] le brancher sur un client MCP existant (Claude Code par exemple)
      et documenter l'intégration ;
- [ ] écrire un **client MCP minimal** (découverte `tools/list`, appel
      `tools/call`) pour comprendre les deux côtés du protocole ;
- [ ] le versant sécurité : que se passe-t-il si un document indexé
      contient une instruction malveillante ? (**prompt injection
      indirecte** — à documenter, c'est un sujet d'entretien).

**Livrable** : repo `homelab-mcp`.
**CV** : « authored an MCP server and client » — déjà demandé tel quel
dans des offres.

### Module 6 — Production : evals, traces, sécurité *(continu, à partir du module 2)*

Pas un projet séparé : une exigence transverse à intégrer aux modules 2-5.

- [ ] self-hoster **Langfuse** (un conteneur de plus) et tracer les appels
      des modules 2 et 3 : latence, tokens, coût équivalent ;
- [ ] lire et savoir restituer l'**OWASP Top 10 for LLM Applications** ;
- [ ] mener un **test adversarial** sur son propre RAG/agent (injections
      dans les documents, dans les entrées) et documenter les défenses ;
- [ ] écrire une page « threat model » de l'agent Jarvis (déjà à moitié
      fait dans securite.md — la traduire en vocabulaire métier) ;
- [ ] (option, pour comprendre — pas prioritaire pour l'emploi visé)
      un **fine-tuning LoRA** d'un petit modèle sur Colab, pour savoir
      dire en entretien ce que c'est et quand c'est (rarement) la bonne
      réponse.

### Module 7 — Multimodal : capitaliser sur le pipeline vocal *(2-3 semaines, après le module 2)*

Le homelab fait déjà du multimodal (Whisper/Piper) — ce module transforme
l'acquis en compétence démontrable et ajoute la vision :

- [ ] **documenter l'existant en vocabulaire métier** : le pipeline vocal
      de Jarvis comme étude de cas STT/TTS (latences mesurées par brique,
      choix des modèles, streaming Piper) — un post « anatomy of a fully
      local voice assistant » ;
- [ ] **vision** : faire tourner un VLM local via Ollama (Qwen-VL ou
      LLaVA sur la RTX 2060) — décrire une photo, lire un document
      scanné ; mesurer ce qui rentre en 6 Go ;
- [ ] (bonus homelab) brancher une caméra dans HA → « Jarvis, décris ce
      que tu vois » ; ou OCR des documents famille vers le NAS ;
- [ ] situer les API cloud équivalentes (vision GPT/Claude/Gemini,
      DALL-E / Nano Banana, Whisper API) pour en parler en entretien.

**Livrable** : post/README + démo vision locale.
**CV** : « runs a fully local multimodal pipeline (STT, TTS, vision) on
consumer hardware ».

---

## 6. Le portfolio — transformer le travail en employabilité

1. **Un GitHub public en anglais** avec les repos des modules. Chaque
   README : le problème, l'architecture (un schéma), les métriques, ce
   que vous referiez autrement. Le repo homelab lui-même peut avoir une
   vitrine publique expurgée (pas d'IP, pas de détails famille —
   cohérent avec [workflow doc](../README.md)).
2. **Écrire** : un post par module (blog perso ou dev.to). « Building a
   RAG over my homelab docs, with evals » attire exactement les bons
   recruteurs. La qualité de doc déjà démontrée dans ce repo est un
   avantage compétitif réel — l'exploiter.
3. **Le pitch entretien**, en une phrase : *« J'ai construit un assistant
   vocal + agentique 100 % local de A à Z — inférence GPU, pipeline
   multimodal, RAG évalué, agent sandboxé, serveur MCP — et je peux vous
   expliquer chaque couche sans framework. »*
4. **Certifications** : aucune n'est indispensable sur ce créneau. Si une
   seule : un badge cloud générique (AWS/GCP) aide pour les entreprises
   qui déploient sur le cloud, mais toujours derrière le portfolio, jamais
   à la place.

---

## 7. Veille — rester à jour (prolonge jarvis.md §10)

- **Modèles & inférence** : r/LocalLLaMA, releases Ollama/vLLM, blog HF.
- **Ingénierie & carrière** : newsletters Pragmatic Engineer, Latent
  Space ; blogs d'ingénierie (Anthropic, notamment sur les agents et MCP) ;
  [roadmap.sh/ai-engineer](https://roadmap.sh/ai-engineer) (référentiel
  vivant — re-comparer avec §9 tous les 6 mois).
- **Agents & protocoles** : spec MCP (modelcontextprotocol.io), repo Pi,
  annonces Agent Skills / OKF.
- **Sécurité** : OWASP GenAI, Simon Willison (référence prompt injection).
- Consigner dans le vault Obsidian (notes `type: watch`) — la veille
  devient de la mémoire agent, et des sujets de posts.

---

## 8. Vue d'ensemble du calendrier

| Ordre | Module | Durée indicative | Dépend de |
|---|---|---|---|
| 1 | Socle sans framework | 2-3 sem. | — |
| 2 | RAG + evals | 1 mois | 1 |
| 3 | Agent maison (Pi) | 1-2 mois | 1 (et Phase 2 Jarvis pour la mémoire) |
| 4 | vLLM / infra | 2 sem. | — (parallélisable) |
| 5 | Serveur + client MCP | 1-2 sem. | 2 (réutilise le RAG) |
| 6 | Production (evals/traces/sécu) | continu | démarre avec 2 |
| 7 | Multimodal | 2-3 sem. | 2 (parallélisable ensuite) |

Soit ~5-7 mois à rythme soirées/week-ends pour un profil **complet et
différencié** : capable de produire chaque couche, avec les preuves
publiques pour le démontrer.

---

## 9. Correspondance avec roadmap.sh/ai-engineer

Couverture du référentiel [roadmap.sh/ai-engineer](https://roadmap.sh/ai-engineer)
(extrait le 11 juillet 2026) par ce document — pour vérifier qu'aucun
sujet attendu du marché n'est angle mort :

| Section roadmap.sh | Ici |
|---|---|
| Introduction (AI Engineer vs ML Engineer, rôles) | §3 |
| Common Terminology (LLM, inférence, training, AI vs AGI…) | §2 couche 0 |
| Working with LLMs (prompt vs context engineering, sampling, CoT, ReAct…) | §2 couche 0 |
| AI Models (types, fermés/ouverts, choisir son modèle) | §2 couche 1 |
| Platforms & Ecosystem (APIs natives, HF, Ollama, LM Studio, OpenRouter) | §2 couches 1 et 4 |
| How LLMs Work | §2 couche 0 + réf. Karpathy/3B1B |
| Embeddings & Vector Databases (cas d'usage, modèles, bases) | §2 couche 2 + module 2 |
| RAGs (chaîne, RAG vs fine-tuning, frameworks) | §2 couche 2 + module 2 |
| AI Agents (boucle, ReAct, SDKs, multi-agents) | §2 couche 3 + modules 1 et 3 |
| Model Context Protocol (host/client/serveur, transports) | §2 couche 4 + module 5 |
| Multimodal AI (vision, audio, STT/TTS, génération) | §2 couche M + module 7 |
| AI Safety and Ethics (injection, biais, modération, adversarial) | §2 couche T + module 6 |
| Evaluation & Observability (types d'evals, régression, outils) | §2 couche T + modules 2 et 6 |
| Development Tools (Claude Code, Cursor, Codex…) | §4 |
| Pre-requisites (frontend/backend/full-stack) | §4 |

Ce que ce document ajoute par rapport au référentiel : la couche
inférence approfondie (vLLM, quantization — leur section est légère),
le sandboxing d'agents, les harnais (Pi), les skills, le fil rouge
homelab et l'angle portfolio/entretien.

---

## 10. Ce que disent les offres réelles — relevé de terrain (juillet 2026)

Enquête menée le 11 juillet 2026 sur **France Travail** (14 offres pour le
mot-clé « LLM »), **HelloWork** (9 offres « Ingénieur LLM ») et **Welcome
to the Jungle**. Sept offres lues intégralement, du stage au poste
d'architecte : STEP UP (Ingénieur LLM Senior, Annecy), MARGO Conseil
(AI Engineer, Paris), GRDF (Maître d'œuvre plateforme LLM/MCP/Agents),
Groupe Carso (alternance IA générative), MEENT (workflows agentiques,
Strasbourg), Cenova (GenAI Engineer RAG & MCP, Neuilly), Mirakl
(Senior AI Engineer agentic commerce, Paris/Bordeaux).

### 10.1 Les technos réellement exigées (par fréquence dans l'échantillon)

| Compétence / techno | Présence | Détail tel qu'exigé dans les offres |
|---|---|---|
| **Python production-grade** | quasi 100 % | pas « savoir scripter » : tests, packaging, code review, « software craftsmanship » (MARGO), venv/Git même en alternance (Carso) |
| **RAG en production** | quasi 100 % | chaîne complète nommée : ingestion, chunking, embeddings, vector DB, retrieval, génération — plus **hybrid search, re-ranking, filtres métadonnées, grounding/citations/hallucinations, multilingue** (Cenova, STEP UP) |
| **Agents / agentic AI** | quasi 100 % | tool calling, workflows multi-étapes, **multi-agents**, human-in-the-loop, gestion du contexte (STEP UP, MARGO, Mirakl, MEENT) |
| **Frameworks d'orchestration** | ~80 % | LangChain et LlamaIndex cités partout ; montée de **LangGraph** ; aussi Haystack, AutoGen, **Pydantic AI**, LangFlow, **Vercel AI SDK** |
| **MCP nommé explicitement** | ~60 % ⚠️ | GRDF (plateforme MCP), Cenova (« mise en œuvre de MCP »), Carso (stack), Mirakl, une offre Bordeaux dédiée « connecteurs MCP ». Le pari du module 5 est déjà gagné |
| **Evals / LLMOps** | ~70 % | « frameworks d'évaluation » (STEP UP), « pipelines d'évaluation continue » en CI/CD (MARGO), monitoring hallucinations/pertinence/latence/**coûts**, A/B testing, rollbacks (Cenova) ; outils : LangSmith, MLflow, Arize, Langfuse |
| **Bases vectorielles** | ~70 % | nommées : Qdrant, Pinecone, Weaviate, Milvus, Chroma, FAISS — « au moins une » maîtrisée |
| **Docker / CI/CD** | ~80 % | Kubernetes en plus chez MARGO et GRDF |
| **FastAPI / APIs backend** | ~50 % | intégration SI (ERP, CRM, bases documentaires) — le LLM ne vit jamais seul |
| **Cloud (AWS/Azure/GCP)** | ~60 % | AWS **Bedrock** (STEP UP), Azure OpenAI, GCP — « maîtrise d'une des principales plateformes » (Cenova) |
| **Guardrails / sécurité IA** | ~40 % | gateway LLM, guardrails, « cybersécurité IA, attaques spécifiques aux LLM, **RGPD** » (GRDF) |
| **Prompt engineering avancé** | ~50 % | few-shot, chain-of-thought cités tels quels (STEP UP) ; « prompt management : versionnage, gouvernance » (GRDF) |
| **TypeScript/Node.js** | ~20 % | principal chez STEP UP (SDK IA interne), bonus ailleurs — confirme « Python d'abord, TS en second » |
| **Fine-tuning** | ~25 % | toujours secondaire : « sélection et fine-tuning des modèles » — jamais le cœur du poste |

### 10.2 Expérience, salaires, accès au métier

- **Les CDI demandent 4 à 7 ans d'expérience** (dev, data science ou ML)
  *dont une expérience récente LLM* — le titre « AI Engineer » se prend
  rarement en premier poste.
- **Les portes d'entrée junior existent** : alternances et stages très
  exigeants techniquement (Carso demande à un alternant : LangChain,
  Qdrant, MCP, FastAPI, Docker) — le niveau de ce document correspond.
- **Salaires relevés** : 40-60 k€ (Strasbourg, ESN), 50-55 k€ (Annecy),
  50-79 k€ (Paris, conseil), 70-90 k€ (manager, Paris), 65-75 k€
  (Bruxelles).
- **Qui recrute** : majoritairement des **ESN/cabinets** (STEP UP, MARGO,
  Cenova, MEENT, Infogène, Triskell, Talan…), puis l'industrie et le
  service public qui internalisent (GRDF, Veolia, Carso, DINUM « IA
  souveraine ») et les éditeurs produits (Mirakl, Doctolib, ManoMano).

### 10.3 Signaux forts à exploiter

1. **Mirakl demande un lien GitHub dans le CV.** La stratégie portfolio
   (§6) n'est pas un pari, c'est un critère de sélection formalisé.
2. **« Production, pas des PoC »** revient mot pour mot (MARGO, Cenova,
   Mirakl). Chaque module doit se raconter en termes de mise en
   production : monitoring, coûts, robustesse — pas de démo jetable.
3. **GRDF construit littéralement un Jarvis d'entreprise** : gateway
   multi-modèles (= le [routeur multi-modèles](../architecture/router-multi-model.md)),
   guardrails, mémoire, RAG, prompt management, MCP, agents. Le homelab
   est une réplique 1:1 des plateformes que les grands groupes montent —
   argument d'entretien à formuler exactement ainsi.
4. **La souveraineté/RGPD valorise le local** : offres DINUM « IA
   souveraine », cyber IA + RGPD chez GRDF — savoir déployer du LLM
   **on-premise** est un différenciateur français, pas une lubie.
5. **Soft skills systématiques** : vulgariser auprès de non-techniciens,
   veille active documentée, autonomie, **anglais professionnel** (écrit
   partout, oral pour les boîtes internationales).

### 10.4 Ajustements de la roadmap suite à l'enquête

- [ ] **Ajouter des notions cloud** (le seul vrai angle mort du homelab
      local-only) : savoir *situer* AWS Bedrock / Azure OpenAI / Vertex AI
      (offres managées de LLM), et idéalement un petit déploiement d'un
      module sur un free tier — sans en faire un chantier.
- [ ] **LangGraph** à ajouter explicitement au module 2/3 (monte plus
      vite que prévu dans les offres).
- [ ] Au module 2, pousser le retrieval jusqu'au **re-ranking et aux
      filtres métadonnées** (exigés tels quels par les offres seniors).
- [ ] Au module 6, ajouter le suivi des **coûts** dans Langfuse (métrique
      citée dans toutes les offres LLMOps).
- [ ] En entretien/CV, employer les termes des offres : « production-grade »,
      « human-in-the-loop », « grounding », « pipelines d'évaluation
      continue », « gateway multi-modèles ».

> *Document vivant : cocher, dater, ajuster les durées au réel, et y
> reporter ce que la veille (§7) rend obsolète — comme pour le reste du
> homelab.*

# Roadmap AI Engineer — socle technique d'apprentissage

> **Rôle de ce document** : feuille de route de formation pour maîtriser la
> stack LLM complète (inférence, orchestration, agents, production), avec un
> double objectif : être capable de **produire chaque couche soi-même**, et
> être **opérationnel et demandé sur le marché du travail** (profil
> AI Engineer). Le homelab (Jarvis) sert de terrain d'entraînement et de
> portfolio — voir [architecture/jarvis.md](architecture/jarvis.md).
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
   démo, pas de l'ingénierie. Les evals sont LE différenciateur (§6.2).

---

## 2. La stack complète — carte des couches

```
Couche T  PRODUCTION (transverse) : evals, observabilité, sécurité, coûts
Couche 4  PROTOCOLES : API OpenAI-compatible, MCP, function calling
Couche 3  AGENTS : boucle outils, harnais (Pi, Claude Code), sandboxing
Couche 2  ORCHESTRATION : RAG, embeddings, bases vectorielles,
          LangChain / LlamaIndex, pipelines, structured outputs
Couche 1  INFÉRENCE : vLLM, llama.cpp, Ollama, quantization, GPU
Couche 0  FONDAMENTAUX : tokens, attention, context window, sampling
```

### Couche 0 — Fondamentaux (comprendre, pas produire)

Ce qu'un AI Engineer doit savoir *expliquer* (pas re-dériver les maths) :

- **Tokenisation** : le modèle ne voit pas des mots. Conséquences
  pratiques : coûts, limites, pourquoi le comptage de lettres échoue.
- **Attention / transformer** : intuition du mécanisme, pourquoi le
  contexte coûte quadratiquement, ce qu'est le **KV cache**.
- **Fenêtre de contexte** : ce qui s'y passe (prompt système + historique
  + outils + documents), pourquoi elle déborde, stratégies (compaction,
  résumé) — vécu concret : le rejet de MCP par Pi pour son coût en contexte.
- **Sampling** : temperature, top_p — ce que « déterministe » veut dire (et
  ne veut pas dire).
- **Embeddings** : projeter du texte dans un espace vectoriel où « proche »
  = « sémantiquement similaire ». Le socle du RAG.
- **Quantization** : q4_K_M et compagnie — troquer de la précision contre
  de la VRAM. Déjà pratiqué (Qwen3 4B sur la RTX 2060).

📚 Références : 3Blue1Brown (série transformers), Karpathy (« Let's build
GPT », « Intro to LLMs »), le playground de tokenizer d'OpenAI/HF.

### Couche 1 — Inférence : faire tourner le modèle

| Outil | Nature | À maîtriser pour |
|---|---|---|
| **llama.cpp** | moteur C++, GGUF, CPU-friendly | comprendre la quantization, le local léger |
| **Ollama** | surcouche conviviale de llama.cpp | déjà acquis (homelab) — API REST, gestion modèles |
| **vLLM** | serveur de production GPU (batching continu, PagedAttention) | les offres « LLM infra » ; savoir servir un modèle à N utilisateurs |
| **HF Transformers** | bibliothèque Python de référence | charger/inspecter un modèle à la main, comprendre ce que les serveurs enrobent |

Notions clés : débit (tokens/s) vs latence, batching, KV cache, VRAM
(poids + cache + contexte), choix CPU/GPU.

### Couche 2 — Orchestration : câbler le LLM dans une application

**C'est là que sont la majorité des postes.** Le cœur du métier AI Engineer :

- **RAG** (Retrieval-Augmented Generation) : chunking, embeddings,
  base vectorielle (Qdrant, pgvector, Chroma), retrieval (similarité,
  hybride BM25+vecteurs, re-ranking), injection en contexte, citations.
- **Structured outputs** : forcer du JSON valide (JSON mode, schémas,
  Pydantic), valider, réessayer. Indispensable dès qu'un LLM alimente
  du code.
- **Frameworks** : **LlamaIndex** (centré RAG), **LangChain/LangGraph**
  (chaînes et graphes d'appels) — à connaître parce que le marché les
  demande, en sachant dire quand un script de 80 lignes suffit.
- **Pipelines batch** : traitement en masse (classification, extraction,
  tagging) avec reprise sur erreur et validation des sorties.

### Couche 3 — Agents : le LLM qui agit

- **La boucle d'agent** : réfléchir → appeler un outil → lire le résultat
  → recommencer. À écrire soi-même une fois (pattern Pi : 4 outils,
  une boucle while).
- **Function calling / tool use** : définir des outils (schémas JSON),
  parser les appels, exécuter, renvoyer.
- **Harnais existants** : Pi, Claude Code, Hermes — savoir les utiliser
  est un prérequis générique ; savoir les **étendre** (extensions, hooks,
  skills) et les **confiner** est une compétence.
- **Sandboxing et garde-fous** : moindre privilège, interception des
  appels d'outils (hook `tool_call` de Pi), conteneurs, validation
  humaine des actions destructives. Voir
  [architecture/securite.md](architecture/securite.md) §5 — les
  non-négociables du homelab sont exactement les bonnes pratiques métier.

### Couche 4 — Protocoles : la glu

- **API OpenAI-compatible** : le standard de fait pour parler à un moteur
  d'inférence (Ollama, vLLM, llama.cpp l'exposent tous) — c'est elle qui
  rend les couches interchangeables.
- **MCP** (Model Context Protocol) : JSON-RPC 2.0 + découverte d'outils
  standardisée (`tools/list`, `tools/call`), transports stdio/HTTP.
  Le standard qui monte dans les offres. Savoir **écrire un serveur MCP**
  est un livrable rapide et très visible (§5, module 5).
- **Skills** (standard Agent Skills) : `SKILL.md` + frontmatter, divulgation
  progressive — le format portable pour donner du savoir-faire à un agent.

### Couche T — Production (transverse, ce qui fait le senior)

- **Evals** : jeux de test question/réponse attendue, scoring
  (exactitude, LLM-as-judge), non-régression avant/après chaque
  changement. Outils : promptfoo, ragas, ou un script maison assumé.
- **Observabilité** : tracer chaque appel (prompt, réponse, latence,
  tokens, coût). Outils : Langfuse (self-hostable ✅), OpenTelemetry.
- **Sécurité LLM** : prompt injection (direct et indirect), exfiltration
  par outil, **OWASP Top 10 for LLM Applications** — à connaître par cœur,
  c'est un sujet d'entretien de plus en plus fréquent et le homelab est
  un cas d'école (agent + bash + fichiers famille).
- **Coûts et dimensionnement** : estimer tokens/mois, choisir
  local vs API, petit vs gros modèle par tâche (le routeur multi-modèles
  de [architecture/router-multi-model.md](architecture/router-multi-model.md)
  est ce raisonnement appliqué).

---

## 3. Le marché — où sont les postes, comment ils s'appellent

| Intitulé | Cœur du poste | Couches | Volume d'offres |
|---|---|---|---|
| **AI Engineer / LLM Engineer** | brancher des LLM sur les données et process d'une entreprise : RAG, agents, evals, mise en prod | 2, 3, 4, T | ⭐⭐⭐ le gros du marché |
| **LLM Infra / MLOps GPU** | servir des modèles : vLLM, GPU, K8s, monitoring, coûts | 1, T | ⭐⭐ moins d'offres, moins de candidats |
| **ML Engineer / Data Scientist LLM** | fine-tuning, entraînement, données | 0-1 + maths | ⭐ marché plus petit, plus exigeant |
| **Développeur « augmenté »** | dev classique + maîtrise des outils IA | 3 (usage) | prérequis générique, pas un métier |

**Mots-clés qui reviennent dans les offres AI Engineer (2026)** : RAG,
embeddings, vector database, LangChain/LlamaIndex, function calling,
agents, MCP, evals, prompt engineering, FastAPI, Python, Docker.
Côté infra : vLLM, quantization, CUDA (notions), Kubernetes, Terraform.

**Ce qui trie les candidats en entretien** (dans l'ordre) :

1. « Comment évaluez-vous votre système ? » — 90 % n'ont pas de réponse.
2. « Expliquez ce qui se passe quand le modèle appelle un outil » — au
   niveau HTTP/JSON, pas au niveau « le framework s'en occupe ».
3. « Votre RAG répond mal : comment diagnostiquez-vous ? » (retrieval ?
   chunking ? prompt ? modèle ? — démarche de debug par couche).
4. « Quels risques de sécurité pour un agent avec accès fichiers ? »
5. Un repo GitHub qui tourne, documenté, avec des métriques.

**Atouts déjà en main** (à assumer dans un CV) : self-hosting complet,
Docker, GPU/quantization en pratique, architecture réseau et sécurité
raisonnées, documentation de qualité professionnelle — le repo homelab
en est la preuve.

---

## 4. Compétences transverses — les prérequis

- **Python d'abord** : tout l'écosystème couche 2/T est en Python.
  Niveau visé : à l'aise avec venv/uv, typing, Pydantic, `httpx`/`requests`,
  async de base, tests pytest. **FastAPI** pour exposer ses services
  (le standard des micro-services IA).
- **TypeScript en second** : les harnais (Pi, SDKs Anthropic/OpenAI)
  et le front. Utile, pas prioritaire.
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
(`http://192.168.1.57:11434`, voir [architecture/reseau.md](architecture/reseau.md)) :

- [ ] un chat en CLI avec historique de conversation (gestion du contexte
      à la main : troncature, résumé) ;
- [ ] du **function calling à la main** : définir 2-3 outils en schéma
      JSON, parser la sortie du modèle, exécuter, renvoyer le résultat ;
- [ ] une **mini-boucle d'agent** (pattern Pi) : read/write/edit/bash
      dans une boucle while, ~200 lignes ;
- [ ] du **structured output** : extraction d'infos en JSON validé
      Pydantic, avec retry en cas de JSON invalide.

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
      automatisé, tableau de non-régression v1 → v2 → v3. *C'est la
      partie la plus valorisable du module.*

**Livrable** : repo `homelab-rag` avec le tableau de métriques dans le
README.
**CV** : « built and evaluated a RAG pipeline end-to-end (custom, then
Qdrant + LlamaIndex), with regression evals ».

### Module 3 — L'agent maison : « Hermes sur base Pi » *(1-2 mois, = Phase 3 Jarvis)*

Fusion formation × roadmap Jarvis (voir
[architecture/jarvis.md](architecture/jarvis.md) §7) :

- [ ] extension Pi **hook `tool_call`** : liste noire de commandes
      destructives + validation humaine — le non-négociable de
      [architecture/securite.md](architecture/securite.md) §5 ;
- [ ] **outil custom `home_assistant`** (`pi.registerTool`) appelant
      l'API REST de HA avec un token à périmètre limité ;
- [ ] **mémoire versionnée** : hooks `session_start`/`session_shutdown`
      → git pull/commit sur le dépôt mémoire (convention OKF) ;
- [ ] **conteneur dédié** à l'agent, moindre privilège, aucun accès aux
      partages famille ;
- [ ] (bonus) mode **RPC/SDK** : un petit service qui tient une session
      Pi ouverte — l'embryon d'agent persistant.

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

### Module 5 — Un serveur MCP *(1 semaine, gros rendement)*

- [ ] écrire un **serveur MCP en Python** exposant le homelab en
      lecture : état des conteneurs, entités HA, recherche dans la doc
      (réutilise le module 2 !) ;
- [ ] le brancher sur un client MCP (Claude Code par exemple) et
      documenter l'intégration ;
- [ ] (bonus) le versant sécurité : que se passe-t-il si un document
      indexé contient une instruction malveillante ? (prompt injection
      indirecte — à documenter, c'est un sujet d'entretien).

**Livrable** : repo `homelab-mcp`.
**CV** : « authored an MCP server » — déjà demandé tel quel dans des offres.

### Module 6 — Production : evals, traces, sécurité *(continu, à partir du module 2)*

Pas un projet séparé : une exigence transverse à intégrer aux modules 2-5.

- [ ] self-hoster **Langfuse** (un conteneur de plus) et tracer les appels
      des modules 2 et 3 ;
- [ ] lire et savoir restituer l'**OWASP Top 10 for LLM Applications** ;
- [ ] écrire une page « threat model » de l'agent Jarvis (déjà à moitié
      fait dans securite.md — la traduire en vocabulaire métier) ;
- [ ] (option, pour comprendre — pas prioritaire pour l'emploi visé)
      un **fine-tuning LoRA** d'un petit modèle sur Colab, pour savoir
      dire en entretien ce que c'est et quand c'est (rarement) la bonne
      réponse.

---

## 6. Le portfolio — transformer le travail en employabilité

1. **Un GitHub public en anglais** avec les repos des modules. Chaque
   README : le problème, l'architecture (un schéma), les métriques, ce
   que vous referiez autrement. Le repo homelab lui-même peut avoir une
   vitrine publique expurgée (pas d'IP, pas de détails famille —
   cohérent avec [workflow doc](README.md)).
2. **Écrire** : un post par module (blog perso ou dev.to). « Building a
   RAG over my homelab docs, with evals » attire exactement les bons
   recruteurs. La qualité de doc déjà démontrée dans ce repo est un
   avantage compétitif réel — l'exploiter.
3. **Le pitch entretien**, en une phrase : *« J'ai construit un assistant
   vocal + agentique 100 % local de A à Z — inférence GPU, RAG évalué,
   agent sandboxé, serveur MCP — et je peux vous expliquer chaque couche
   sans framework. »*
4. **Certifications** : aucune n'est indispensable sur ce créneau. Si une
   seule : un badge cloud générique (AWS/GCP) aide pour les entreprises
   qui déploient sur le cloud, mais toujours derrière le portfolio, jamais
   à la place.

---

## 7. Veille — rester à jour (prolonge jarvis.md §10)

- **Modèles & inférence** : r/LocalLLaMA, releases Ollama/vLLM, blog HF.
- **Ingénierie & carrière** : newsletters Pragmatic Engineer, Latent
  Space ; blogs d'ingénierie (Anthropic, notamment sur les agents et MCP).
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
| 5 | Serveur MCP | 1 sem. | 2 (réutilise le RAG) |
| 6 | Production (evals/traces/sécu) | continu | démarre avec 2 |

Soit ~4-6 mois à rythme soirées/week-ends pour un profil **complet et
différencié** : capable de produire chaque couche, avec les preuves
publiques pour le démontrer.

> *Document vivant : cocher, dater, ajuster les durées au réel, et y
> reporter ce que la veille (§7) rend obsolète — comme pour le reste du
> homelab.*

# Progression — homelab-rag (Module 2)

> **Double rôle** : (1) re-briefer Claude en début de session — *commencer
> chaque session par « lis PROGRESSION.md »* — et (2) consolider
> l'apprentissage d'Anthony en rendant le parcours visible.
> **Tenu à jour par Claude à chaque étape franchie.**
> Roadmap complète : [../roadmap.md](../roadmap.md) (ce projet = Module 2).
> Module précédent : [../llm-from-scratch/PROGRESSION.md](../llm-from-scratch/PROGRESSION.md).
> Dernière mise à jour : 20 juillet 2026

---

## Le projet

Un RAG sur la doc du homelab : poser « qu'est-ce qu'on avait décidé pour
le backup du NAS ? » et obtenir une réponse **sourcée** depuis les `.md`
de ce repo. Trois versions successives (à la main → Qdrant → LlamaIndex),
avec des **evals dès la v1** — la partie la plus valorisable du module.

- Corpus : les `.md` du repo homelab (architecture/, serveurs/, guides/,
  exploration/…) — ~17 fichiers de vraie doc.
- Embeddings : via l'Ollama de jarvis-central (`http://192.168.1.57:11434`),
  modèle `nomic-embed-text` (à puller — constat du 20 juillet : seul
  Qwen3 4B est présent).
- Génération : Qwen3 4B, comme au Module 1.
- Outillage : mise + venv auto (même mise.toml que le Module 1), httpx.

## Checklist v1 — le RAG entièrement à la main

- [ ] **01_embeddings.py** — premier embedding : texte → vecteur via
      `/api/embed` ; regarder la forme du résultat (dimensions, valeurs)
- [ ] **02_similarite.py** — similarité cosinus écrite à la main ;
      vérifier que « proche en sens » = « score élevé » sur des phrases test
- [ ] **03_chunking.py** — découper les `.md` du repo en chunks
      (par sections markdown), avec le fichier source gardé en métadonnée
- [ ] **04_indexer.py** — pipeline chunk → embedding → SQLite
      (l'index complet du corpus, reconstructible)
- [ ] **05_rechercher.py** — question → embedding → top-k chunks
      les plus proches (le « R » de RAG, sans génération)
- [ ] **06_rag.py** — la chaîne complète : retrieval → prompt avec
      contexte → réponse avec citations des fichiers sources
- [ ] **Evals v1** — jeu de ~30 questions/réponses attendues sur la doc,
      score automatisé (déterministe + LLM-as-judge), baseline chiffrée

## Checklist v2 — Qdrant + retrieval hybride

- [ ] migrer le stockage vers **Qdrant** (conteneur docker sur le homelab)
- [ ] retrieval hybride (BM25 + vecteurs), re-ranking, filtres métadonnées
- [ ] re-passer les evals : tableau comparatif v1 → v2

## Checklist v3 — LlamaIndex + outillage standard

- [ ] refaire la chaîne en **LlamaIndex** ; documenter ce que le framework
      apporte / cache
- [ ] passer le jeu d'evals dans **RAGAS** ou **DeepEval**
- [ ] tableau final v1 → v2 → v3 dans le README
- [ ] réponse d'entretien rédigée : **RAG vs fine-tuning**, pourquoi RAG ici

## Notions acquises (validées en pratique)

| Notion | Vue dans | L'essentiel |
|---|---|---|
| _(à remplir au fil des étapes)_ | | |

## Points de vigilance / à revoir

- Leçon du Module 1 (exercice 08) : pour les exercices denses, fournir un
  **squelette à trous** ou découper en sous-fonctions — c'est l'assemblage
  qui coûte, pas la syntaxe.
- Les énoncés d'exercices doivent **spécifier toutes les valeurs attendues**.
- `nomic-embed-text` : ajouté à `deploiement/jarvis-central/installer.sh`
  (config-as-code, réflexe d'Anthony) — déployer via commit + git pull +
  `./installer.sh` sur jarvis-central avant le premier script.

## Conventions du projet

- Scripts numérotés `NN_sujet.py`, docstring pédagogique en tête,
  commentaires en français sans accents dans le code (compat encodage
  console Windows).
- Chaque étape : Claude explique le concept → écrit/teste le script →
  Anthony bidouille → questions → cocher ici.

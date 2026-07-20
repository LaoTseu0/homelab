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

- [x] **01_embeddings.py** — premier embedding : texte → vecteur via
      `/api/embed` ; 768 dims quelle que soit la longueur du texte,
      norme toujours égale à 1
- [x] **02_similarite.py** — `similarite_cosinus()` **écrite par Anthony
      du premier coup** (squelette à trous, protocole de test fourni avec
      valeurs attendues — les 5 paires OK) ; détour pédagogique réussi par
      la géométrie (schémas + widget interactif : flèches, Pythagore,
      produit scalaire = alignement, division par les normes = on ne garde
      que l'angle)
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
| Embedding = coordonnées du sens | 01 | texte → vecteur 768 floats (analogie RGB : ressemblance devenue distance calculable) ; taille fixe quelle que soit la longueur du texte ; aucune dimension n'a de sens seule |
| Vecteurs Ollama normés à 1 | 01 | `/api/embed` renvoie des vecteurs de norme 1 (vérifié) → le dénominateur du cosinus vaut ~1, cos ≈ produit scalaire |
| Norme = Pythagore en 768D | 02 | somme des carrés = longueur² ; `sqrt` défait les carrés pour revenir à une longueur |
| Produit scalaire = alignement | 02 | somme des produits terme à terme ; grand si les flèches sont d'accord, 0 si perpendiculaires, négatif si opposées — mais mélange direction et longueur |
| Cosinus = angle pur | 02 | produit scalaire / (norme × norme) : la division retire les longueurs, seule la direction (le sens) reste |
| `zip(v1, v2)` + expression génératrice | 02 | parcourir deux listes en parallèle ; `sum(a*b for a, b in zip(...))` = produit scalaire en une ligne |
| L'espace est multilingue | test 02 | question FR vs sa traduction EN : 0.81, la paire la plus proche du banc — le sens a une position, pas la langue ; un RAG FR peut interroger de la doc EN |
| Le score absolu ne veut rien dire | test 02 | backup NAS vs tarte aux pommes : 0.53, pas 0 — les scores se tassent dans une bande étroite ; **seul le classement compte** (d'où le top-k, jamais de seuil absolu) |

## Points de vigilance / à revoir

- Leçon du Module 1 (exercice 08) : pour les exercices denses, fournir un
  **squelette à trous** ou découper en sous-fonctions — c'est l'assemblage
  qui coûte, pas la syntaxe. **Validé sur l'exercice 02** : fonction juste
  du premier coup.
- Anthony apprend mieux avec du **visuel** : les schémas (SVG/widgets
  interactifs) pour les concepts géométriques/abstraits ont très bien
  fonctionné pour produit scalaire/norme/cosinus — réutiliser l'approche
  (chunking, espace vectoriel, HNSW à venir).
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

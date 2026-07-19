# Progression — llm-from-scratch

> **Double rôle** : (1) re-briefer Claude en début de session — *commencer
> chaque session par « lis PROGRESSION.md »* — et (2) consolider
> l'apprentissage d'Anthony en rendant le parcours visible.
> **Tenu à jour par Claude à chaque étape franchie.**
> Roadmap complète : [../roadmap.md](../roadmap.md) (ce projet = Module 1).
> Dernière mise à jour : 19 juillet 2026

---

## Contexte du parcours

- Anthony apprend **Python et les LLM en partant de zéro** (background :
  homelab, Docker, HA, notions JS/Node via mise).
- Méthode : incrémental, chaque script introduit UN mécanisme LLM et
  quelques notions Python, commentaires en français dans le code.
- Le code appelle l'**Ollama de jarvis-central** (`http://192.168.1.57:11434`,
  modèle `qwen3:4b-instruct-2507-q4_K_M`). jarvis-core (RTX 4090) volontairement
  laissé de côté pendant l'apprentissage.
- Outillage : **mise** (pas uv) — `mise.toml` épingle Python 3.12 et
  auto-active le venv `.venv/` en entrant dans le dossier.

## Checklist Module 1 — le socle sans framework

- [x] **01_hello.py** — premier appel LLM : POST JSON → réponse JSON
- [x] **02_chat.py** — chat CLI avec historique : modèle stateless,
      l'historique est renvoyé en entier à chaque tour, compteur de tokens
- [x] **Streaming** — afficher la réponse token par token (03_stream.py ;
      compteur de tokens = **premier code Python écrit par Anthony**, avec
      `.get()` défensif spontané)
- [ ] **Sampling** — temperature, top-k, top-p : expérimenter et noter
      *(bon candidat pour un premier notebook Jupyter)*
- [ ] **Gestion du contexte** — troncature puis résumé/compaction de
      l'historique
- [ ] **Function calling à la main** — 2-3 outils en schéma JSON, parser,
      exécuter, renvoyer (= comprendre ReAct)
- [ ] **Mini-boucle d'agent** — read/write/edit/bash dans une boucle while
- [ ] **Structured output** — extraction JSON validée Pydantic, retry si
      invalide
- [ ] **README anglais** — livrable portfolio (extraire en repo dédié ?)

## Notions acquises (validées en pratique)

| Notion | Vue dans | L'essentiel |
|---|---|---|
| Un appel LLM = JSON aller-retour | 01_hello | POST {modèle, messages} → {message} ; tout le reste est de l'habillage |
| Ollama = serveur, pas outil de dev | session 1 | API HTTP sans auth, ouverte sur le LAN (restriction 127.0.0.1 = dette consciente) |
| Modèle **stateless** | 02_chat | aucune mémoire entre 2 appels ; la « conversation » est une liste côté client renvoyée en entier |
| Croissance du contexte | 02_chat | prompt_eval_count grossit à chaque tour (49 → 97 tokens sur 2 tours) ; d'où troncature/compaction à venir |
| venv ≠ VM | session 1 | juste un dossier de dépendances par projet (analogie node_modules) ; jamais versionné |
| httpx | session 1 | bibliothèque HTTP (équiv. curl/fetch), choisie pour son mode async futur |
| Petit modèle = limites visibles | bidouillage | Qwen3 4B q4 est « teubé » par taille, pas par nature — parfait pour voir les mécanismes et les échecs |
| Streaming = 1 ligne JSON par morceau | 03_stream | le modèle génère token par token ; `iter_lines` + `json.loads` ; l'affichage streame mais l'historique veut le texte recollé (`"".join`) |
| `dict.get(clé, défaut)` vs `dict[clé]` | exercice 03 | `.get` ne plante pas si la clé manque — réflexe défensif face aux données externes |

## Questions posées par Anthony (et réponses clés)

- **Notebook ?** → document interactif code+texte+résultats (Jupyter) ;
  utile pour expérimenter, pas le quotidien ; prévu pour l'étape sampling.
- **Python dynamique comme JS ?** → dynamique OUI, mais **fortement** typé
  (`"1" + 1` = TypeError, pas `"11"`) ; type hints optionnels = TS intégré,
  vérifiés par l'éditeur, ignorés à l'exécution ; Pydantic validera à
  l'exécution (module 1, structured output).
- **Async existe ?** → oui, même syntaxe que JS, mais **synchrone par
  défaut** (l'inverse de Node) ; opt-in via asyncio ; on l'apprendra avec
  FastAPI / appels concurrents, pas avant.
- **Grande fenêtre = pleine pertinence ?** → non : *lost in the middle*,
  dilution de l'attention, + compaction par le harnais. D'où le « context
  engineering ».

## Points de vigilance / à revoir

- Premier code écrit par Anthony le 19 juillet (exercice 03) : correct du
  premier coup, indentation comprise. **Continuer à augmenter la part de
  code écrite par lui à chaque étape.**
- Subtilité vue en passant : `print("\n")` = 2 sauts de ligne (le `\n` +
  celui de `print`) ; `print()` seul = 1.

## Conventions du projet

- Scripts numérotés `NN_sujet.py`, docstring pédagogique en tête,
  commentaires en français sans accents dans le code (compat encodage
  console Windows).
- Chaque étape : Claude explique le concept → écrit/teste le script →
  Anthony bidouille → questions → cocher ici.

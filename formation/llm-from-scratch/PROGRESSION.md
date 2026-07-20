# Progression — llm-from-scratch

> **Double rôle** : (1) re-briefer Claude en début de session — *commencer
> chaque session par « lis PROGRESSION.md »* — et (2) consolider
> l'apprentissage d'Anthony en rendant le parcours visible.
> **Tenu à jour par Claude à chaque étape franchie.**
> Roadmap complète : [../roadmap.md](../roadmap.md) (ce projet = Module 1).
> Dernière mise à jour : 20 juillet 2026

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
- [x] **Sampling** — temperature, top-k, top-p (04_sampling.ipynb, premier
      notebook ; exercice réussi avec un protocole en dict de scénarios +
      `**option` écrit par Anthony seul ; incident « génération débridée »
      → garde-fou `num_predict` + section supervision au backlog homelab)
- [x] **Gestion du contexte** — troncature puis résumé/compaction
      (05_contexte.py : compaction déboguée en live — trace du résumé,
      placement en system ; `tronquer()` écrite par Anthony via slicing,
      validée sur spec ; compaction éprouvée sur une vraie conversation)
- [x] **Function calling à la main** — 06_outils.py : heure_actuelle,
      calculer (eval filtré), et `modeles_charges` **écrit par Anthony de
      bout en bout** (fonction httpx.get + schéma JSON + dispatch) ; il a
      aussi ajusté num_predict 400→800 de lui-même
- [x] **Mini-boucle d'agent** — 07_agent.py : sandbox workspace/ +
      garde anti path-traversal, validation humaine des commandes shell,
      MAX_TOURS ; `ecrire_fichier` **écrit par Anthony** (try/except
      au-delà de la spec) ; incidents analysés : typo du modèle dans un
      argument, rm→del auto-corrigé, « suppression niée » malgré preuve
- [x] **Structured output** — 08_structured.py : demander poliment vs
      décodage contraint (`format` Ollama) vs validation Pydantic ;
      `extraire()` avec retry **écrite par Anthony** (ternaire Python
      spontané) ; banc d'essai : 0 retry en contraint, retries
      systématiques en poli, auto-correction observée en live
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
| Défauts de sampling en couches | debug 04 | le Modelfile du modèle impose ses défauts (`/api/show` : temp 0.7, top_p 0.8…) ; une option absente de la requête y retombe — régler la temperature sans neutraliser top_p/top_k masque son effet |
| Méthodologie de debug | debug 04 | hypothèses → test discriminant → une variable à la fois — formalisée dans [../../guides/methodologie-debug.md](../../guides/methodologie-debug.md) avec l'étude de cas complète |
| Ordre du pipeline de sampling | exercice 04 | prompt → probabilités → filtres top-k/top-p → temperature → tirage ; `top_k=1` rend la temperature inopérante ; `top_p=0.5` ≈ greedy sur du factuel (noyau réduit au favori) |
| Autorégression sans retour arrière | exercice 04 | un mauvais token tiré (« hélium ») devient du contexte : le modèle ne peut pas effacer, il « se corrige » en public — génération de gauche à droite, sans brouillon |
| Seed = pseudo-aléatoire reproductible | exercice 04 | `seed=42` → 3 sorties identiques ; base des tests de non-régression LLM |
| Borner toute génération | incident 04 | sampling débridé + question ouverte = génération sans fin, GPU à fond ; `num_predict`/`max_tokens` obligatoire dans toute app sérieuse |
| `list` vs `dict` | relecture 04 | dict à clés 0..n = liste déguisée ; `for x in liste:` sans `range(n)` — dict pour chercher par nom, list pour parcourir en ordre |
| Compaction = LLM au service de sa propre mémoire | 05_contexte | résumer les vieux échanges par un appel LLM, repartir de [system + résumé] ; 420 → 184 tokens dans le test |
| Sans trace, pas de diagnostic | debug 05 | rappel échoué après compaction : impossible de trancher « résumé fautif ou modèle fautif » sans afficher le résumé — l'observabilité d'abord |
| Le placement dans le contexte compte | debug 05 | résumé parfait ignoré en message *user* (réflexe « je ne stocke rien »), exploité en message *system* — l'autorité de la voix system est un outil |
| Slicing de liste | exercice 05 | `messages[-4:]` = les 4 derniers ; `[x] + liste` concatène — `tronquer()` en 2 lignes |
| La spec peut être fausse | exercice 05 | le « cas limite trivial » de l'énoncé dupliquait le message system — code fidèle à une spec trouée = bug quand même |
| Le modèle propose, le code dispose | 06_outils | un tool_call est une *demande* JSON ; c'est notre code qui exécute et renvoie (role `tool`) — le modèle ne fait toujours que générer du texte |
| La description d'outil = contrat de routage | 06_outils | le modèle choisit uniquement sur nom+description ; description trop large = mauvais routage (« disponibles » ≠ « chargés en VRAM ») |
| Entrées non fiables & dispatch | 06_outils | nom et arguments viennent du modèle → dict FONCTIONS comme barrière, filtrage avant eval — premiers réflexes de sandboxing |
| Savoir s'abstenir | tests 06 | « présente-toi » → zéro outil appelé : la pertinence du non-appel se teste aussi |
| Agent = LLM + outils + boucle while | 07_agent | la boucle de 06 copiée telle quelle ; seule la *nature* des outils change (lire des infos → agir sur le monde) |
| Sandbox & path traversal | 07_agent | `(SANDBOX / nom).resolve()` + `is_relative_to` : le « ../../secrets » du modèle est bloqué — analogie volume Docker |
| Validation humaine (human-in-the-loop) | 07_agent | commande shell montrée + confirmation clavier ; un refus est renvoyé au modèle comme information, sinon il croit avoir agi |
| Les arguments d'outils sont générés, donc faillibles | incident 07 | « laotseu.txt » demandé → le modèle écrit `laoseu.txt` : typo dans un tool_call — entrée non fiable, version sournoise |
| L'erreur d'outil est un feedback exploitable | test 07 | `rm` échoue (Windows) → le modèle lit l'erreur, diagnostique, retente avec `del` : la boucle s'auto-corrige |
| Les outils fiabilisent les données, pas le raisonnement | incident 07 | listing prouvant la suppression sous les yeux, le modèle conclut l'inverse — ancré sur son propre doute précédent (autorégression à l'échelle de la conversation) |
| Un résultat d'outil doit être explicite | incident 07 | `del` réussit en silence → « aucune sortie » est ambigu pour le modèle ; renvoyer le returncode lève l'ambiguïté |
| `for ... else` Python | 07_agent | le `else` d'une boucle s'exécute si elle finit *sans* `break` — idéal pour détecter MAX_TOURS atteint ; n'existe pas en JS |
| Décodage contraint = filtre grammatical | 08_structured | le `format` d'Ollama masque les tokens qui violeraient le schéma — un filtre de plus dans le pipeline de sampling du 04 ; 0 retry en contraint vs retries systématiques en « demande polie » |
| La contrainte garantit la forme, pas le fond | banc 08 | `ram_go: 32` omis (champ optionnel, la grammaire l'autorise), `role: ''` qui passe la validation, `services: ['formation']` inventé — d'où `Field(min_length=1)` et la validation sémantique |
| Pydantic = type hints exploités à l'exécution | 08_structured | `class Serveur(BaseModel)` + `model_validate_json` = json.loads + vérif des types + objet construit ; la réponse concrète à « Python typé comme JS ? » |
| Le retry sur erreur de validation | 08_structured | ValidationError renvoyée au modèle comme information → il corrige (`role: null` → corrigé) ; même mécanique que rm→del en 07 |
| Nos consignes ont des effets de bord | banc 08 | « mets null si une info est absente » → le modèle sur-applique et met null sur des champs requis — le prompt est aussi à déboguer |
| Une classe est une valeur | 08_structured | `extraire(texte, Serveur)` : la classe se passe en argument, comme une fonction en JS ; premier usage de classes et d'héritage du parcours |

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
  premier coup, indentation comprise. Exercice 04 : protocole complet en
  autonomie (dict de scénarios, `**option` réutilisé côté appelant).
  Exercice 07 : `ecrire_fichier` correcte du premier coup, avec un
  try/except autour de `write_text` **au-delà de la spec** — réflexe
  défensif devenu spontané.
  **Continuer à augmenter la part de code écrite par lui à chaque étape.**
- Mini-bidouille proposée (07) : enrichir le retour de
  `executer_commande` avec `resultat.returncode` pour lever l'ambiguïté
  des commandes silencieuses — à faire ou non avant l'étape suivante.
- Exercice 08 : code final correct (ternaire spontané en prime) mais
  Anthony signale avoir **eu du mal à l'écrire** — c'était l'exercice le
  plus dense (construction de messages + boucle + try/except + raise en
  une fonction). Diagnostic posé avec lui : ce n'est **ni la syntaxe ni
  la logique, c'est l'assemblage** (traduire une spec multi-étapes en un
  tout cohérent). Pour les prochains exercices denses : fournir un
  squelette à trous (la structure donnée, les lignes à remplir) ou
  découper en sous-fonctions exercées une à une.
- Feedback d'Anthony sur l'exercice 04 : énoncé pas assez précis, il a dû
  choisir des valeurs « au pif ». **Les énoncés d'exercices doivent
  spécifier toutes les valeurs attendues** (ou dire explicitement que le
  choix fait partie de l'exercice).
- Subtilité vue en passant : `print("\n")` = 2 sauts de ligne (le `\n` +
  celui de `print`) ; `print()` seul = 1.
- Piège notebook vécu : les sorties affichées sous une cellule datent du
  dernier run — ne jamais s'y fier sans réexécuter.

## Conventions du projet

- Scripts numérotés `NN_sujet.py`, docstring pédagogique en tête,
  commentaires en français sans accents dans le code (compat encodage
  console Windows).
- Chaque étape : Claude explique le concept → écrit/teste le script →
  Anthony bidouille → questions → cocher ici.

# Méthodologie de debug — hypothèses et tests discriminants

> **Rôle de ce document** : la démarche générale pour diagnostiquer un
> comportement aberrant, illustrée par un cas réel (sampling Ollama,
> 19 juillet 2026, formation Module 1). Complète le debug par couches du
> [pipeline vocal](debug-pipeline-vocal.md). C'est aussi la démarche
> attendue en entretien AI Engineer (« votre RAG répond mal : comment
> diagnostiquez-vous ? » — [roadmap §3](../formation/roadmap.md)).

---

## 1. La boucle de diagnostic

1. **Constater précisément** — noter le symptôme exact, pas une impression.
   « La temperature n'a aucun effet ET temp=0 n'est pas reproductible »
   est un constat ; « ça marche pas » n'en est pas un.
2. **Lister les hypothèses plausibles** — toutes, même celles qu'on
   n'aime pas : bug dans mon code ? option mal transmise ? serveur qui
   ignore l'option ? défaut caché quelque part ?
3. **Choisir le test le plus discriminant** — celui dont le résultat
   *élimine* le plus d'hypothèses d'un coup, pas celui qui est le plus
   facile à lancer. Un bon test a une prédiction écrite AVANT de le
   lancer : « si X, alors on verra A ; sinon B ».
4. **Isoler les variables** — ne changer qu'UNE chose à la fois ; fixer
   tout le reste explicitement (ne pas laisser des défauts implicites
   décider à votre place — c'est précisément ce qui nous a piégés, §3).
5. **Conclure et documenter** — la cause racine, le correctif, et la
   leçon transférable. Un debug non documenté sera refait dans 6 mois.

## 2. Les règles d'or

- **Lire le message d'erreur en entier** avant toute autre chose.
- **Interroger le système, pas sa mémoire** : l'API/la machine dit ce qui
  EST ; la doc et les souvenirs disent ce qui DEVRAIT être.
- **Se méfier des défauts implicites** : tout paramètre non fixé a une
  valeur quelque part, décidée par quelqu'un d'autre.
- **Un résultat « impossible » = une hypothèse fausse dans votre modèle
  mental**, pas un caprice de la machine. C'est une information, pas un bruit.
- **Reproduire avant de corriger** : un bug qu'on ne sait pas déclencher
  n'est pas compris.

## 3. Étude de cas — « la temperature ne fait rien » (Ollama, qwen3:4b)

**Symptôme** : mêmes réponses à `temperature=0.0` et `1.5` ; et à `0.0`,
sorties différentes d'un appel à l'autre (alors que temp 0 = greedy =
reproductible attendu).

**Hypothèses** : (a) bug dans notre code Python (options mal envoyées) ;
(b) Ollama ignore les options de la requête ; (c) un défaut caché
interfère ; (d) `0.0` traité comme « non renseigné » (piège classique de
la valeur zéro en Go).

| # | Test | Prédiction | Résultat | Hypothèses éliminées |
|---|---|---|---|---|
| 1 | `/api/show` sur le modèle | — (collecte d'info) | le Modelfile embarque `temperature 0.7, top_k 20, top_p 0.8` | révèle (c) : il EXISTE des défauts cachés |
| 2 | `seed=42` deux fois | si options honorées → 2 sorties identiques | identiques ✓ | (a) et (b) éliminées — le transport fonctionne |
| 3 | `temperature=0.0` trois fois | si (d) → sorties variées | 3 sorties identiques | (d) éliminée |
| 4 | `temperature=1.5` + `top_p=1.0, top_k=0` (défauts neutralisés) | si (c) → variété retrouvée | 4 essais, 4 réponses différentes | **cause racine confirmée** |

**Cause racine** : les options de la requête écrasent les défauts du
Modelfile *paramètre par paramètre*. En ne réglant que la temperature, le
`top_p=0.8` du Modelfile restait actif et tronquait la distribution aux
favoris — masquant l'effet d'une haute temperature.

**Leçon transférable** : les réglages s'empilent en couches (défauts du
moteur ← Modelfile ← requête). Pour étudier une variable, neutraliser
explicitement les autres.

## 4. Boîte à outils — interroger un serveur Ollama

L'API répond à tout client HTTP ; trois façons équivalentes de poser la
même question :

```powershell
# PowerShell — la fiche complete d'un modele (parametres du Modelfile,
# template de chat, licence...) : c'est le test n°1 de l'etude de cas
Invoke-RestMethod -Method Post -Uri http://192.168.1.57:11434/api/show `
  -Body '{"model":"qwen3:4b-instruct-2507-q4_K_M"}' -ContentType 'application/json'
```

```bash
# curl (depuis n'importe quelle machine du LAN)
curl http://192.168.1.57:11434/api/show \
  -d '{"model":"qwen3:4b-instruct-2507-q4_K_M"}'
```

```bash
# CLI ollama (en SSH sur jarvis-central) — même info, mise en forme
ollama show qwen3:4b-instruct-2507-q4_K_M
```

Les autres endpoints de diagnostic :

| Endpoint | Donne |
|---|---|
| `GET /api/version` | version du serveur (pour corréler avec les changelogs) |
| `GET /api/tags` | modèles installés + taille de contexte + capacités (tools…) |
| `POST /api/show` | paramètres Modelfile, template, détails d'un modèle |
| `GET /api/ps` | modèles chargés en mémoire en ce moment (VRAM utilisée) |

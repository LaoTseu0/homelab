# Inférence locale — notes d'exploration

> Condensé d'une conversation de conception, juillet 2026 — le fourre-tout
> d'exploration de l'architecture d'inférence. Le décidé est distillé au fur
> et à mesure dans [../architecture/inference.md](../architecture/inference.md).
> Matériel : `jarvis-core` (Ryzen 9 7900X, RTX 4090 24 Go, 64 Go RAM) +
> `jarvis-central` (Ryzen 5, RTX 2060 6 Go, 32 Go RAM), reliées en Ethernet filaire.
> Dernière mise à jour : 18 juillet 2026
> Statut : **exploration — rien n'est monté, le modèle pour la RTX 4090
> n'est pas choisi.** Décisions raisonnées, pas des résultats mesurés :
> tout ce qui est chiffré ici est à revérifier sur la machine.

---

## 1. Le catalogue de modèles, remis à jour

Le point de départ de la conversation était un avis d'IA basé sur un catalogue de fin 2025 (Qwen3 32B, Llama 3.2, Gemma 3, Phi-4-mini). L'architecture proposée était saine ; les modèles étaient périmés.

### Les modèles « top » ne sont pas pour toi

| Modèle | Taille | Sur une 4090 |
|---|---|---|
| GLM-5.2 | 744B total / ~40B actifs, contexte 1M, MIT | Non — 238 Go en 2-bit, 3-9 tok/s avec offload |
| MiniMax-M3 | ~428B / ~23B actifs, 128 experts, multimodal | Non |
| Kimi K2.6 | ~1T | Non (ne rentre même pas sur un Mac 512 Go) |
| DeepSeek V4 Pro | — | Non |

**Le piège MoE, qui n'est pas intuitif :** même si seulement ~23B de paramètres s'activent par token, **l'intégralité des poids doit résider en mémoire**. On ne peut pas paginer un expert inactif vers le disque sans une latence qui tue l'inférence interactive. « 23B actifs » décrit la *vitesse*, pas l'*empreinte*.

→ Deux chiffres à ne jamais confondre : **paramètres totaux = est-ce que ça rentre ?** / **paramètres actifs = à quelle vitesse ?**

### La stack retenue

```
VRAM 24 Go  →  Qwen3.6-27B Q4_K_M        (~17 Go, 45-55 tok/s)   résident, 90 % de l'usage
            →  Qwen3-Coder 30B-A3B        alternative code (262K contexte natif)
            →  Gemma 4 12B QAT            (~7 Go) vision + AUDIO, à la demande
            →  gpt-oss 20B Q5             (~15 Go) si besoin de tool-calling très propre

RAM 56 Go   →  gpt-oss 120B Q4, offload MoE  (~15-25 tok/s)  chat/raisonnement, prompts COURTS

API         →  GLM-5.2 quand le frontier est vraiment nécessaire (~$1.40/$4.40 par M tokens)
```

### Notes par modèle

- **Qwen3.6-27B** — le meilleur choix réaliste pour 24 Go. ~77 SWE-Bench Verified. Dépasse des MoE bien plus gros sur le codage agentique.
- **Gemma 4 12B** (sorti le 3 juin 2026, Apache 2.0, contexte 256K) — architecture *encoder-free* : la vision et l'audio entrent directement dans le backbone, sans encodeurs séparés. **Premier modèle de taille moyenne avec audio natif** — c'est sa seule vraie raison d'être dans ta stack. Prendre la version **QAT** (quantization-aware training), meilleure qu'un GGUF quantifié après coup. Livré avec des drafters MTP (décodage spéculatif gratuit).
  → Attention : « tout le monde dit qu'il est top » signifie « top pour un laptop 16 Go ». Tu as 24 Go. Ce n'est pas ton modèle principal.
- **gpt-oss 120B** — le seul modèle >100B réellement utilisable chez toi, grâce à ~5B actifs seulement.

### Deux erreurs classiques à éviter

- **L'obsession du 70B est dépassée.** Qwen3.6-27B en Q5 bat Llama 3.3 70B en IQ2 pour la moitié de la VRAM.
- **Le contexte à 128K fait exploser le cache KV** (+8-12 Go en plus du modèle). Plafonner à 64K.

---

## 2. L'offload MoE

**Le principe :** exploiter l'asymétrie d'un MoE.
- Le **tronc commun** (attention, embeddings) est petit mais traversé à chaque token → **VRAM**.
- Les **experts** (FFN) = 90-95 % des poids, mais seule une poignée sert par token → **RAM système**.

Sur un modèle **dense**, ça ne marche pas : tous les poids servent à chaque token.

Implémentation : `llama.cpp`, flag `--n-cpu-moe N` (ou l'ancien `-ot "\.ffn_.*_exps\.=CPU"`). Vérifier la syntaxe avec `--help`, ça bouge.

**La formule qui décide de tout :**

```
tok/s ≈ bande_passante_RAM ÷ (params_actifs × bits_par_param ÷ 8)
```

**Le budget est VRAM + RAM**, pas RAM seule. Avec 64 Go (~56 utilisables) + 24 Go VRAM ≈ 80 Go.

### La bonne nouvelle du 64 Go

64 Go sur AM5 = probablement 2×32 Go. Le 7900X est dual-channel → **2 DIMMs = configuration optimale**, DDR5-6000 stable en EXPO. Avec 4 DIMMs (128 Go), tu serais retombé à 3600-4000.

→ Moins de place, mais ce qui rentre tourne **plus vite** (~65-70 Go/s réels au lieu de ~57).

### Le piège que personne ne mentionne

Tout ce qui précède concerne la **génération** (decode), qui est *bandwidth-bound*.
Le **prefill** (traitement du prompt d'entrée) est *compute-bound* — et là, le CPU s'effondre.

| Usage | Contexte | Offload MoE ? |
|---|---|---|
| Chat, rédaction, questions ponctuelles | ~500 tokens | ✅ excellent |
| Batch nocturne | peu importe | ✅ |
| Agentique (Cline, analyse de repo) | 30-80K retraités à chaque tour | ❌ plusieurs minutes par appel |

**Conséquence directe : RAG systématique + offload MoE ne se combinent pas.** (voir §6)

### À vérifier en premier

```bash
sudo dmidecode -t memory | grep -E "Speed|Size"
```
Si tu vois 4800 au lieu de 6000 → profil EXPO désactivé dans le BIOS. **25 % de perte sèche sur tout l'offload, gratuite à récupérer.**

---

## 3. L'architecture à deux machines

### Le piège : ne pas agréger

Réflexe naturel : « 24 + 6 = 30 Go de VRAM ». Non.

`llama.cpp` a un mode RPC qui distribue les couches en réseau. Ça marche, mais :
- La 2060 fait ~336 Go/s contre ~1008 Go/s pour la 4090 → les couches qui y atterrissent deviennent le goulot de **tout** le modèle.
- Ce n'est pas la bande passante réseau qui tue (les activations font quelques Ko/token), c'est la **latence de synchronisation** × nombre de couches distantes × chaque token.
- Tu ajoutes 6 Go à un pool de 24 pour ralentir l'ensemble de 30-50 %.
- Même en agrégeant tout (~112 Go), tu n'atteins pas Qwen3 235B Q4 (130 Go). **Tu ne débloques rien.**

**→ Deux machines : spécialiser, pas agréger.**

### Le découpage

```
      pc-admin (client)
              |  LAN filaire
              v
  ┌─────────────────────────────────┐
  │  jarvis-central — "front door"  │   Ryzen 5 / 2060 6 Go / 32 Go
  │  allumée 24/7                   │
  │  • Open WebUI                   │
  │  • Orchestrateur / API          │
  │  • BGE-M3 embeddings            │  ~2.2 Go VRAM
  │  • Reranker (bge-v2-m3)         │  ~2.2 Go VRAM  ← le vrai besoin GPU
  │  • faster-whisper (STT)         │  ~1.5 Go VRAM
  │  • Qdrant + Postgres            │  RAM
  │  • Indexation RAG (cron)        │
  └───────────┬─────────────────────┘
              │  HTTP, réveil Wake-on-LAN
              v
  ┌─────────────────────────────────┐
  │  jarvis-core — "le moteur"      │   Ryzen 9 / 4090 / 64 Go
  │  ne fait QUE de l'inférence     │
  └─────────────────────────────────┘
```

⚠️ Budget VRAM de la 2060 serré : embeddings + reranker + Whisper ≈ 5,9 Go sur 6. Arbitrer — Whisper peut tomber sur le CPU du Ryzen 5, il encaisse.

### Ce que ça débloque

- **Le routeur trouve sa maison** : sur la 2060, avec le modèle d'embedding déjà chargé. Coût marginal nul.
- **Le système ne s'arrête plus** : pendant que jarvis-core est monopolisée par gpt-oss 120B, l'interface et le RAG tournent sur jarvis-central.
- **jarvis-core peut dormir** : jarvis-central la réveille en WoL (30-60 s + chargement). Surtout : jarvis-central reste allumée pour l'indexation nocturne pendant que jarvis-core est éteinte.

### Ce que la 2060 ne fait PAS

Elle n'offre pas un « petit modèle pour requêtes simples ». À 6 Go tu tiens un 4B Q4, et un 4B qui répond mal coûte plus cher en re-prompts qu'il n'économise.
**La hiérarchie « petit / moyen / gros modèle » de l'archi initiale ne se justifie pas ici.** Ton 27B fait 45-55 tok/s. Route vers **un seul** modèle.

---

## 4. GPU AMD 16 Go : décision = non

Le rôle de jarvis-central demande ~4-6 Go. La 2060 le fait déjà. 16 Go dans ce slot = 10 Go qui ne servent à rien.

Et en faire un nœud d'inférence ne tient pas : 16 Go = classe 13-14B, à côté d'une machine qui fait tourner un 27B à 50 tok/s. **Aucune capacité ajoutée, juste une redondance plus lente.**

### Le blocage concret

**faster-whisper repose sur CTranslate2, qui est CUDA-only** — pas de backend ROCm. Le nœud STT ne démarre pas. Repli : `whisper.cpp` (Vulkan/ROCm, plus lent). Même logique pour bitsandbytes, exllamav2, flash-attention — CUDA-first.
→ *À revérifier avant tout achat, ça peut avoir bougé.*

### À décharge

ROCm 7.2 (mars 2026) : première version avec support officiel RDNA 4, parité out-of-the-box Ollama / llama.cpp / vLLM, installeur unique Windows + Linux. Compter 75-85 % du débit NVIDIA. `llama.cpp` en ROCm/HIP = Linux uniquement mais plus rapide ; en Vulkan = partout, compatibilité plus large.

Mais le verdict des tests récents tient : **n'utiliser AMD que si on a déjà de l'AMD, ou sur une affaire imbattable**, avec 5-10 h à prévoir pour débugger drivers et compilation. Et deux stacks de drivers à maintenir (CUDA sur jarvis-core, ROCm sur jarvis-central) **double le coût d'ops** — qui est le vrai coût de cette archi.

### Le meilleur usage de cet argent

Le maillon faible n'est pas la 2060, ce sont **les 24 Go de jarvis-core**. Une 3090 d'occasion (24 Go) → **48 Go poolés** → un 70B dense Q4, ou 27B + Coder résidents simultanément, ou du contexte 128K sans exploser. `llama.cpp` fait du layer-split sans NVLink, même bus PCIe, pas de latence réseau.

**C'est la seule dépense qui change ce que le système sait faire.**

⚠️ Prérequis à vérifier AVANT de se projeter (sur jarvis-core) :
- **Alimentation** : 4090 + 3090 ≈ 800 W de pointe → il faut du 1200 W.
- **Slots** : deux x16 physiques câblés en x8/x8, pas un x4 chipset.
- **Marché** : la pénurie GPU/VRAM de 2026 a poussé les prix à la hausse.

**Option préférée : ne rien dépenser pour l'instant.** Monter l'archi avec la 2060, vivre avec deux semaines, laisser le manque réel se manifester.

---

## 5. Embeddings & RAG — les concepts

### L'embedding

**Une** phrase → **un** vecteur (une liste de nombres). BGE-M3 : 1024 dimensions.

Les dimensions ne sont pas interprétables une par une. Seule la **géométrie** a du sens : deux textes de sens proche → deux vecteurs proches. On mesure par **similarité cosinus** (l'angle).

L'intérêt face aux mots-clés :
```
"résilier mon abonnement"  ↔  "annuler ma souscription"
        → ZÉRO mot en commun, mais vecteurs très proches
```

**Un modèle d'embedding n'est pas un LLM.** Un LLM génère token par token, en boucle (500 tokens = 500 passes → 20 s). Un modèle d'embedding fait **une seule passe** → ~10 ms. C'est pour ça que c'est ~1000× moins cher.

### Ce que le RAG est vraiment

> **Le RAG, c'est du copier-coller automatisé.**

Tu pourrais le faire à la main : chercher dans tes docs, copier le passage, le coller dans le chat. Le RAG automatise le *chercher* et le *coller*. Les embeddings ne servent qu'à savoir **quel** passage coller.

**Trois corrections de mental model :**

1. **Ce n'est pas un fichier de vecteurs.** La base stocke le vecteur **et** le texte original. Le vecteur est **l'adresse, pas le contenu** — comme la cote d'un livre. L'embedding n'est pas réversible.
   ```
   { id: "doc42_chunk7",
     vector: [0.021, -0.183, ...],              ← pour CHERCHER
     payload: { text: "Pour résilier, allez...", ← ce qu'on RÉCUPÈRE
                source: "guide.pdf", page: 12 } }
   ```
2. **Le LLM ne voit jamais un vecteur.** Les vecteurs meurent à l'étape de la recherche. Le LLM reçoit du **texte brut** dans un prompt. Il fait ce qu'il a toujours fait : lire du texte, générer la suite.
3. **On n'ajoute rien au LLM.** Le modèle n'est pas modifié d'un octet. Ses poids sont figés. On lui colle le bon extrait sous le nez, juste à temps.

### Où le calcul atterrit vraiment

| Étape | Où | Coût |
|---|---|---|
| Découpage en chunks | CPU | quelques secondes |
| Embedding par lots (indexation) | **GPU utile** | 50K chunks : ~5 min GPU vs ~2 h CPU |
| Stockage Qdrant / HNSW | **CPU + RAM, jamais GPU** | 100K chunks × 1024 dim × 4 o = **400 Mo** |
| Embedding de la question | GPU ou CPU | 10 ms vs 50-100 ms → **sans importance** |
| Recherche vectorielle | **CPU + RAM** | ~5 ms (parcours de graphe, pas du deep learning) |
| Reranker | **GPU réel** | ~100 ms GPU vs 2-3 s CPU |
| Génération LLM | **VRAM** | ~20 s → **99 % du coût** |

**→ Le RAG n'a pas besoin de VRAM.** Le GPU ne sert qu'à **l'indexation** et au **reranker**. C'est la seule raison d'être GPU de jarvis-central.

### Bi-encodeur vs cross-encodeur

- **Embedding (bi-encodeur)** : encode question et document **séparément**. Pré-calculable. Rapide.
- **Reranker (cross-encodeur)** : passe la paire `(question, document)` **ensemble**, avec attention croisée. Bien plus précis, non pré-calculable.

Pattern standard : recherche vectorielle → 50 candidats en 5 ms → reranker → garde les 5 meilleurs.

### La limite des embeddings

Bons pour le **sens**, mauvais pour **l'exact**. Cherche `ERR_4021` ou un numéro de facture : l'embedding « floute » ces tokens rares et ramène du vaguement similaire.

**→ La recherche hybride (BM25 mots-clés + vecteurs, fusionnés par RRF) est le standard, pas une optimisation.** Sans elle : magique deux jours, puis frustrant.

---

## 6. Le RAG en pratique

### L'orchestrateur est au centre, pas le LLM

Inverser le sens du contrôle : **ton orchestrateur est au centre, le LLM est une fonction qu'il appelle.** Le LLM est la pièce la plus passive : un serveur HTTP qui reçoit du texte, rend du texte, et **oublie tout**. Il ne sait pas qu'un RAG existe.

### Le RAG, c'est 15 lignes

```python
def repondre(question):
    v = embed(question)                          # ~10 ms
    chunks = qdrant.search(v, limit=5)           # ~5 ms
    contexte = "\n".join(c.payload["text"] for c in chunks)
    prompt = f"Contexte:\n{contexte}\n\nQuestion: {question}"
    return llm.chat(prompt)                      # ~20 s
```

Timing : **~15 ms de RAG, ~20 s de LLM.** Le RAG ne « tourne pas à côté », il s'exécute *avant*, synchrone, puis disparaît.

### Ce qui tourne vraiment : 4 démons indépendants

```
llama.cpp server   :8080   ← modèle en VRAM
serveur embedding  :8081   ← BGE-M3
Qdrant             :6333   ← vecteurs en RAM
orchestrateur      :8000   ← les 15 lignes + l'API
```
Chacun redémarre sans les autres. C'est pour ça que la séparation en deux machines marche : ce sont déjà des services réseau — les déplacer = changer une URL.

### Chercher ≠ injecter

Deux coûts sans rapport :
- **Chercher** : ~15 ms. Gratuit.
- **Injecter** : ~2 500 tokens dans le prompt. Cher.

Le snippet naïf les enchaîne aveuglément. Aucune raison. **Chercher toujours, injecter selon le score :**

```python
def repondre(question):
    chunks = qdrant.search(embed(question), limit=5)
    if chunks[0].score < SEUIL:          # rien de pertinent
        return llm.chat(question)        # prompt nu
    contexte = "\n".join(c.payload["text"] for c in chunks)
    return llm.chat(f"Contexte:\n{contexte}\n\nQuestion: {question}")
```

La recherche vectorielle retourne **toujours** les k plus proches — c'est du plus-proche-voisin, pas un filtre. Une question Python sur une base RH ramènera 5 chunks RH, avec un score catastrophique. **C'est ce signal qu'il faut lire.**

### Pourquoi ça compte (le vrai coût n'est pas les tokens)

En local les tokens sont gratuits. Mais :

1. **Le contexte non pertinent rend le modèle plus bête.** Il *va essayer* d'en tenir compte — on l'a entraîné à croire que le contexte fourni est pertinent. Résultat : des hallucinations **ancrées sur du vrai texte**, bien formatées, indiscernables. Les pires.
2. **Le prefill.** 2 500 tokens ≈ 1-2 s sur la 4090 avec le 27B (supportable). Mais en **offload MoE**, le prefill est compute-bound CPU → **plusieurs dizaines de secondes**. RAG systématique + gpt-oss 120B = incompatible.

### L'échelle des solutions

1. **Seuil de score** — 3 lignes, 80 % du bénéfice. ⚠️ Le cosinus est **mal calibré dans l'absolu** : 0,7 ne veut rien dire en soi, ça dépend du corpus. À régler empiriquement.
2. **Reranker** — sa seconde vie : meilleur **détecteur de non-pertinence**, parce que son score est *calibré* (entraîné sur des paires pertinent/non-pertinent). Bien plus fiable qu'un seuil cosinus.
3. **Classifieur** — la vraie mission du routeur : décider **s'il faut du RAG** (binaire, ~10 ms, modèle d'embedding déjà chargé). Mais le seuil fait le même boulot pour zéro complexité → **sauter cette étape**.
4. **RAG agentique** — donner au LLM un outil `chercher_dans_ma_doc(requête)`. Il peut **reformuler**, chercher plusieurs fois, affiner. `gpt-oss 20B` est taillé pour ça. Coût : +1 aller-retour LLM = +20 s.

**Plan :** seuil maintenant → reranker sur jarvis-central → agentique seulement si la recherche en une passe rate des choses (probablement jamais pour de la doc perso).

---

## 7. RAG vs fine-tuning

> **Le RAG change ce que le modèle *sait*. Le fine-tuning change comment il *se comporte*.**

Ce ne sont pas deux options pour le même problème.

### Le malentendu qui coûte cher

« Je vais fine-tuner sur ma doc pour qu'il la connaisse » = **la mauvaise raison de fine-tuner**, et la plus répandue.

Le fine-tuning n'injecte pas des faits de façon fiable. Il apprend la **forme**. Résultat : un modèle qui a appris le *style* de ta doc et qui invente des fonctionnalités inexistantes, rédigées exactement comme ta vraie doc. **Pire que rien** — les hallucinations deviennent plausibles et indiscernables.

Raison technique : LoRA modifie les poids sur un sous-espace de rang faible. Excellent pour déplacer un *comportement*, mauvais pour *stocker de l'information*.

| | RAG | Fine-tuning |
|---|---|---|
| Modifie le modèle | non | oui |
| Ajouter un doc | ré-indexer, 5 s | tout ré-entraîner |
| Citer ses sources | oui | non |
| Coût | ~0 | GPU + 30 h de dataset |

### Quand le fine-tuning gagne (= du comportement, jamais de la connaissance)

- **Format strict** — toujours du JSON conforme, sans préambule. Prompt : 95 %. Fine-tune : 99,9 %. Si tu parses automatiquement, cet écart est tout.
- **Ton et voix** — intransmissible par prompt. 500 exemples > 500 tokens de description.
- **Savoir tacite** — les règles que tu ne sais pas énoncer. Si tu ne peux pas l'écrire, tu ne peux pas la prompter — mais tu peux la montrer.
- **Distillation** — fine-tuner un 4B sur une tâche étroite que ton 27B fait bien : 95 % de la qualité, 10× la vitesse, 3 Go.
- **Compression de prompt** — un system prompt de 2 000 tokens rejoué à chaque appel, intégré par fine-tuning = ce prefill économisé **à chaque requête**. ← levier direct sur le problème de prefill en offload MoE.

### Le vrai coût n'est pas le GPU

QLoRA sur un 27B en 4-bit tient sur la 4090 (serré : gradient checkpointing, séquences courtes) ; un 12B est confortable. Quelques heures. *Vérifier l'état de l'outillage — Unsloth notamment, ça bouge vite.*

**Le coût, c'est le dataset :** 500-1000 exemples de qualité minimum. À la main, 2 min pièce = **30 heures**. Plus un jeu d'éval séparé. Plus 3-5 itérations, parce que le premier essai ne marche jamais.

Risque réel : **l'oubli catastrophique** — un fine-tune trop étroit dégrade les capacités générales. LoRA à rang faible limite les dégâts, ne les supprime pas.

### L'ordre, non négociable

```
1. Meilleur prompt   →  70 % des cas
2. RAG               →  25 % de plus
3. Fine-tuning       →  les 5 % restants
```

**La quasi-totalité des gens convaincus d'avoir besoin d'un fine-tune ont besoin d'un meilleur prompt.**

### Les deux usages qui te concernent

- **Fine-tuner à mieux *utiliser* le RAG** : citer proprement, dire « je ne sais pas » quand le contexte ne répond pas, ignorer les chunks hors-sujet. Du comportement, pas des faits. Un des usages les plus rentables et des moins pratiqués.
- **Hot-swap LoRA** : un modèle de base en VRAM, des adaptateurs de quelques centaines de Mo échangés en millisecondes. **C'est le vrai « mixture of experts fait maison » sur 24 Go** — les experts sont des *comportements*, pas des modèles. Et là, enfin, le routeur choisit quelque chose de réel : quel adaptateur charger.

---

## 8. Les idées à corriger dans l'archi de départ

| Proposition initiale | Verdict |
|---|---|
| Routeur LLM (Qwen3 1.7B) sur CPU | Sur-ingénierie. 1-3 s de latence *avant* le vrai modèle, pour une décision qu'un classifieur d'embeddings rend en ~10 ms avec plus de précision. Ne se justifie que pour extraire de l'intention structurée. |
| Hiérarchie petit / moyen / gros modèle | Ne tient pas sur 24 Go. Le 27B fait 90 % du boulot à 50 tok/s. Route vers **un** modèle. |
| « À la demande : Coder 32B, vision, 70B » | Coût du swap ignoré : 17-20 Go sur le bus PCIe = **10-30 s de latence** à chaque bascule. Sur 24 Go tu n'as pas de multi-modèles concurrents, tu as un modèle et des changements de contexte coûteux. |
| 70B expérimental | Dépassé. 27B Q5 > 70B IQ2 pour la moitié de la VRAM. |
| « Le routeur sur CPU pour ne pas toucher la 4090 » | Obsolète avec deux machines : la 2060 fait mieux qu'un CPU, gratuitement. |

**Ce qui était juste :** routeur hors de la 4090, VRAM 100 % dédiée au modèle qui répond, l'option « routeur classique » (règles/classifieur) — qu'il présentait comme « moins sexy » alors que c'est le bon choix.

---

## 9. Décisions verrouillantes

Ce sont celles qu'on paie cher si on se trompe.

1. **Le modèle d'embedding.** Changer de modèle = **tout ré-indexer**. Les vecteurs de deux modèles différents vivent dans des espaces incompatibles — même dimension, sens sans rapport. Comparer les deux **ne plante pas**, ça retourne du bruit silencieusement. → Choisir en premier, prévoir de vivre avec.
2. **La stratégie de chunking.** Elle pèse souvent **plus lourd sur le résultat final que le choix du modèle d'embedding**. Sujet dont personne ne parle assez.
3. **CUDA vs ROCm.** Un écosystème entier suit derrière.
4. **Alim + slots de jarvis-core.** Détermine si la 3090 sera un jour possible.

---

## 10. Priorités

### Faire maintenant

1. **Vérifier la fréquence RAM.** `sudo dmidecode -t memory | grep -E "Speed|Size"` — 25 % gratuits si EXPO est off.
2. **Vérifier alim + slots PCIe de jarvis-core.** Décide de l'avenir de l'archi.
3. **Monter le minimum viable** : Qwen3.6-27B sur jarvis-core, Open WebUI sur jarvis-central. Rien d'autre. Envoyer une requête.
4. **Vivre avec pendant deux semaines.** Sans RAG, sans routeur, sans 120B.

### Ensuite, dans l'ordre

5. RAG minimal sur jarvis-central : chunking → BGE-M3 → Qdrant → les 15 lignes.
6. **Écrire 30 questions de test** (15 qui doivent déclencher le RAG, 15 qui ne doivent pas) — **avant** de toucher au seuil.
7. Régler le seuil de score sur ces 30 questions.
8. Recherche hybride (BM25 + vecteurs, RRF). Pas une optimisation : un prérequis.
9. Reranker sur la 2060.
10. gpt-oss 120B en offload — seulement si le 27B échoue sur une classe de requêtes identifiée.

### À approfondir en priorité

- **Le chunking.** Le levier le plus sous-estimé du RAG. Taille, chevauchement, respect de la structure du document, métadonnées.
- **La recherche hybride et le RRF.** Sans ça, `ERR_4021` ne sera jamais trouvé.
- **L'évaluation.** Ce sont des systèmes qu'on **règle**, pas qu'on conçoit. Sans jeu de test, tu règles à l'intuition — et **l'intuition sur les scores de similarité est systématiquement fausse**.
- **Le prefill vs decode.** La distinction qui explique la moitié des décisions de ce document.

### À ne PAS faire maintenant

- Acheter un GPU (AMD ou 3090). Le manque doit se constater, pas s'anticiper.
- Le fine-tuning. Répond à un manque constaté. Si dans un mois tu peux dire « il refuse de sortir du JSON propre » ou « il n'écrit pas comme moi », la question devient réelle — et tu sauras quels 500 exemples écrire, parce que tu auras un mois de conversations ratées à recycler en dataset.
- Le routeur LLM. Le seuil de score fait le même boulot pour zéro complexité.
- Le RAG agentique.

---

## Fiabilité des sources

Une bonne partie des chiffres de ce document (classements, tok/s, prix, VRAM) vient de blogs de comparatifs — dont certains ont un modèle affilié — et de posts communautaires. **Fiable pour les ordres de grandeur, moins pour les scores exacts.**

À savoir aussi : **Artificial Analysis a changé de méthodologie mi-juin 2026** (Intelligence Index v4.1), ce qui a mécaniquement abaissé tous les scores absolus **sans régression des modèles**. → Ne pas comparer des chiffres issus d'articles de dates différentes.

**Tester soi-même sur sa charge réelle avant toute décision d'achat.**

# Architecture — inférence LLM à deux machines

> Comment le homelab sert ses LLM : `jarvis-core` (le moteur) fournit
> l'inférence lourde, `jarvis-central` (la front door) reste l'interface
> 24/7. Distillé depuis [../exploration/inference-locale.md](../exploration/inference-locale.md)
> au fur et à mesure des décisions.
> Dernière mise à jour : 18 juillet 2026
> Statut : **en conception** — répartition des rôles posée ; modèle
> définitif, serveur d'inférence et politique d'alimentation **non tranchés**.

---

## 1. L'intention

Jusqu'ici, tout Jarvis vivait sur `jarvis-central` (RTX 2060 6 Go) — assez
pour la voix/domotique (Qwen3 4B), trop juste pour le raisonnement, le code
et les futurs modèles audio-natifs. L'arrivée de `jarvis-core`
(RTX 4090 24 Go, 64 Go RAM) concrétise le « scale vertical » du principe
directeur n°4 de [jarvis.md](jarvis.md) : la puissance du cerveau avant la
multiplication des pièces.

## 2. Le principe : spécialiser, pas agréger

Le réflexe « 24 + 6 = 30 Go de VRAM » ne fonctionne pas : distribuer un
modèle entre les deux GPU (mode RPC) aligne tout le monde sur la carte la
plus lente et n'ouvre l'accès à aucun modèle supplémentaire. Chaque machine
prend donc le rôle où elle excelle
(raisonnement détaillé : [../exploration/inference-locale.md](../exploration/inference-locale.md) §3).

```
        [ pc-admin / clients ]
                  │  LAN filaire
                  ▼
  ┌───────────────────────────────────────┐
  │  jarvis-central — « front door »      │   RTX 2060 6 Go / 32 Go RAM
  │  allumée 24/7                         │
  │  • pipeline vocal (HA + Wyoming)      │
  │  • Ollama + Qwen3 4B (voix)           │
  │  • orchestrateur / API                │
  │  • RAG : embeddings, reranker,        │
  │    base vectorielle, indexation       │
  └──────────────────┬────────────────────┘
                     │  HTTP (+ réveil Wake-on-LAN envisagé)
                     ▼
  ┌───────────────────────────────────────┐
  │  jarvis-core — « le moteur »          │   RTX 4090 24 Go / 64 Go RAM
  │  ne fait QUE de l'inférence lourde    │
  │  • gros LLM résident (à choisir)      │
  │  • modèles spécialisés à la demande   │
  └───────────────────────────────────────┘
```

## 3. Répartition des rôles

| | `jarvis-central` | `jarvis-core` |
|---|---|---|
| Disponibilité | 24/7 | à la demande (extinction/WoL envisagés) |
| Inférence | Qwen3 4B — voix uniquement (latence < 1 s exigée) | tous les usages lourds : raisonnement, code, agentique |
| Autres services | HA, Wyoming, orchestrateur, RAG complet | aucun — machine mono-mission |
| Écoute réseau | voir matrice de [reseau.md](reseau.md) §4 | SSH + futur port d'API LLM (à définir) |

**Le sens du flux** : `jarvis-central` est *cliente* de `jarvis-core` — pas
l'inverse. Le RAG, lui, n'a pas besoin de grosse VRAM (recherche vectorielle
= CPU/RAM ; seuls l'indexation et le reranker profitent du GPU) : il reste
entièrement sur la front door.

## 4. Stack pressentie sur jarvis-core (à valider)

Candidats issus de l'exploration — **aucun n'est arrêté**, c'est la
prochaine décision à prendre :

| Candidat | Empreinte | Usage visé |
|---|---|---|
| Qwen3.6-27B Q4_K_M | ~17 Go VRAM | modèle résident, ~90 % des requêtes |
| Qwen3-Coder 30B-A3B | — | alternative code (262K de contexte natif) |
| Gemma 4 12B QAT | ~7 Go VRAM | vision + audio natif, à la demande |
| gpt-oss 120B Q4 | VRAM + ~offload RAM | raisonnement, prompts courts uniquement (prefill CPU lent) |

## 5. La tension à arbitrer

Trois exigences ne se satisfont pas simultanément :

```
   voix : réponse < 1 s          « router vers UN seul          jarvis-core éteinte
   en continu, 24/7        vs     modèle » (le 27B fait    vs   quand inutilisée
                                  90 % du travail)              (réveil WoL : 30-60 s)
```

Position actuelle (à confirmer) : le Qwen3 4B **reste sur jarvis-central
pour la voix seule** — c'est le seul usage qui exige la latence du 24/7 ;
tout le reste part sur le modèle unique de `jarvis-core`, quitte à attendre
son réveil.

## 6. Questions ouvertes

1. **Le modèle résident** de jarvis-core (§4) — la décision structurante.
2. **Le serveur d'inférence** : llama.cpp, Ollama ou vLLM ? (l'offload MoE
   du gpt-oss 120B impose llama.cpp ; un usage multi-clients pousserait vLLM).
3. **Le port et l'API exposés** au LAN — et leur restriction UFW à
   `jarvis-central` seule (voir [securite.md](securite.md)).
4. **Politique d'alimentation** : 24/7, extinction manuelle, ou WoL
   déclenché par la front door ?
5. **L'OS de jarvis-core** — même socle qu'un serveur headless
   (Ubuntu Server) ou conservation d'un dual-usage ?

## 7. Prérequis matériels à vérifier avant de trancher

- **Fréquence RAM** : profil EXPO actif (DDR5-6000) — désactivé, c'est
  ~25 % de débit d'offload perdus. Vérification au backlog.
- **Alimentation et slots PCIe** : conditionnent l'option future « second
  GPU 24 Go » (~800 W de pointe à deux cartes, deux slots x8/x8 requis).
- Décision déjà prise : **pas d'achat GPU pour l'instant** — monter
  l'architecture avec l'existant et laisser le manque réel se manifester
  ([../exploration/inference-locale.md](../exploration/inference-locale.md) §4 et §10).

# Homelab — documentation

> Homelab familial 100 % local : un assistant vocal + agentique auto-hébergé
> (« Jarvis ») et les services qui l'entourent (NAS, stockage, réseau).
> Rien n'est exposé à Internet ; tout est versionné ici — architecture,
> procédures d'installation, état courant des machines, guides.

## Les machines

| Machine | Matériel | Rôle |
|---|---|---|
| `jarvis-central` | PC fixe — RTX 2060 6 Go, 32 Go RAM, Ryzen 5 | Pipeline vocal Jarvis (HA + Wyoming + Ollama), « front door » 24/7 |
| `jarvis-core` | Tour — RTX 4090 24 Go, 64 Go RAM | Moteur d'inférence LLM (en préparation — voir [architecture/inference.md](architecture/inference.md)) |
| `nas` | Raspberry Pi 4 — 8 Go | Serveur git (doc + mémoire agents) + partage familial SMB |
| `pc-admin` | PC portable Asus ROG (PC perso) | Administration du homelab en SSH |

Adresses IP et matrice des services : [architecture/reseau.md](architecture/reseau.md)
(référence unique — on ne duplique pas les IP au fil des documents).

## Organisation de la doc

| Emplacement | Contenu | Nature |
|---|---|---|
| [architecture/](architecture/) | Ce qu'on construit et pourquoi : cible, stratégie, sécurité | Stable (statut en en-tête) |
| [exploration/](exploration/) | Notes de travail, pistes non tranchées, comparatifs | Fourre-tout assumé |
| [serveurs/](serveurs/) | Un dossier par machine : `installation.md` (comment ça a été monté) et `etat.md` (ce qui tourne aujourd'hui) | Vivant |
| [deploiement/](deploiement/) | Config **déployable** par machine (compose, services systemd, installeur) — pas de la doc : des fichiers que le serveur exécute | Vivant |
| [guides/](guides/) | Savoir-faire réutilisable (debug, procédures) | Enrichi au fil de l'eau |
| [formation/](formation/) | Parcours AI Engineer adossé au homelab | Vivant |
| [backlog.md](backlog.md) | Tout ce qui reste à faire, par thème | Vivant |
| [archives/](archives/) | Documents historiques, horodatés | Figé |

## Par où commencer

1. Le projet Jarvis, sa démarche et sa stratégie : [architecture/jarvis.md](architecture/jarvis.md)
2. L'architecture d'inférence à deux machines : [architecture/inference.md](architecture/inference.md)
3. Ce qui tourne aujourd'hui sur le serveur : [serveurs/jarvis-central/etat.md](serveurs/jarvis-central/etat.md)
4. La posture de sécurité : [architecture/securite.md](architecture/securite.md)
5. Ce qui reste à faire : [backlog.md](backlog.md)

## Convention des documents

Chaque document a **un rôle et un seul** :

- **architecture/** répond à « que veut-on construire et pourquoi ? »
- **exploration/** répond à « qu'est-ce qu'on envisage, sans avoir tranché ? »
- **installation.md** répond à « comment a-t-on monté ça ? » (figé une fois fait)
- **etat.md** répond à « qu'est-ce qui tourne, là, maintenant ? » (mis à jour à chaque changement)
- **guides/** répond à « comment refaire X quand le besoin revient ? »

Règles transverses :

- Chaque doc porte en en-tête : son rôle, sa date de dernière mise à jour et
  son statut.
- Noms de fichiers en **kebab-case**, extension `.md`.
- Les **lignes de commande** n'apparaissent que dans `serveurs/`,
  `deploiement/` et `guides/` — jamais dans `architecture/` (concepts et
  schémas) ni ici.
- Un bon **schéma** vaut mieux qu'un long paragraphe : les documents
  d'architecture en font un usage systématique.
- **archives/** : nom `AAAA-MM-JJ_sujet.md` (date d'archivage) + en-tête fixe
  (archivé le, origine, conservé pour) ; un fichier archivé ne se modifie
  **plus jamais**.

## Cycle de vie d'une idée

```
[ exploration/ ]──── décision ────►[ architecture/ ]─── mise en œuvre ───►[ serveurs/ ]
  notes, pistes,                     le décidé, citable                   [ deploiement/ ]
  comparatifs                        en confiance                          le réel
       │
       └── une fois distillée ────►[ archives/ ]
                                     horodaté, figé
```

Une idée naît dans `exploration/` ; quand elle est tranchée, sa substance est
distillée dans `architecture/` ; quand elle est montée, le réel est documenté
dans `serveurs/` et `deploiement/` ; la note d'exploration vidée de sa
substance part dans `archives/`.

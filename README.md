# Homelab — documentation

> Homelab familial 100 % local : un assistant vocal + agentique auto-hébergé
> (« Jarvis ») et les services qui l'entourent (NAS, stockage, réseau).
> Rien n'est exposé à Internet ; tout est versionné ici — architecture,
> procédures d'installation, état courant des machines, guides.

## Les machines

| Machine | Matériel | Rôle |
|---|---|---|
| `jarvis-central` | PC — RTX 2060 6 Go, 32 Go RAM, Ryzen 5 | Cerveau de Jarvis : pipeline vocal, LLM, domotique |
| `nas` | Raspberry Pi 4 — 8 Go | Serveur git (doc + mémoire agents) + partage familial SMB |

## Organisation de la doc

| Emplacement | Contenu | Nature |
|---|---|---|
| [architecture/](architecture/) | Ce qu'on construit et pourquoi : cible, stratégie, sécurité | Stable |
| [serveurs/](serveurs/) | Un dossier par machine : `installation.md` (comment ça a été monté) et `etat.md` (ce qui tourne aujourd'hui) | Vivant |
| [deploiement/](deploiement/) | Config **déployable** par machine (compose, services systemd, installeur) — pas de la doc : des fichiers que le serveur exécute | Vivant |
| [guides/](guides/) | Savoir-faire réutilisable (debug, procédures) | Enrichi au fil de l'eau |
| [backlog.md](backlog.md) | Tout ce qui reste à faire, par thème | Vivant |
| [archives/](archives/) | Documents historiques, gardés pour mémoire | Figé |

## Par où commencer

1. Le projet Jarvis, sa démarche et sa stratégie : [architecture/jarvis.md](architecture/jarvis.md)
2. Ce qui tourne aujourd'hui sur le serveur : [serveurs/jarvis-central/etat.md](serveurs/jarvis-central/etat.md)
3. La posture de sécurité : [architecture/securite.md](architecture/securite.md)
4. Ce qui reste à faire : [backlog.md](backlog.md)

## Convention des documents

Chaque document a **un rôle et un seul** :

- **architecture/** répond à « que veut-on construire et pourquoi ? »
- **installation.md** répond à « comment a-t-on monté ça ? » (figé une fois fait)
- **etat.md** répond à « qu'est-ce qui tourne, là, maintenant ? » (mis à jour à chaque changement)
- **guides/** répond à « comment refaire X quand le besoin revient ? »

Chaque doc porte en en-tête : son rôle, sa date de dernière mise à jour et son statut.

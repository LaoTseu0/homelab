# Déploiement — NAS (miroir GitHub)

> **Source de vérité** : ce dossier ; les dépôts bare de `/srv/git/` n'en
> reçoivent que des copies via `installer-miroir.sh`.
> Ne jamais éditer le hook directement sur le NAS — la modification serait
> écrasée au prochain déploiement, et perdue pour les autres dépôts.

## Contenu

| Fichier | Déployé vers | Rôle |
|---|---|---|
| `post-receive` | `/srv/git/<depot>.git/hooks/` | Recopie vers GitHub les refs modifiées ; diagnostique les échecs |
| `installer-miroir.sh` | — | Installe le hook sur tout dépôt ayant un remote `github` (idempotent) |

## Déployer (ou re-déployer après un git pull)

Sur le NAS, en tant que `pinas` :

```bash
cd ~/homelab/deploiement/nas
./installer-miroir.sh
```

Le script ignore les dépôts sans remote `github`, saute ceux déjà à jour, et
sauvegarde l'ancien hook en `post-receive.bak` avant tout écrasement.

## Vérifier

```bash
md5sum ~/homelab/deploiement/nas/post-receive /srv/git/*/hooks/post-receive
```

Toutes les sommes des dépôts miroités doivent être identiques à la première.

## Pour comprendre

- Le modèle (NAS source de vérité, GitHub copie en lecture) :
  [../../architecture/nas.md](../../architecture/nas.md) §4
- Le hook ligne à ligne, et quoi faire quand le miroir décroche :
  [../../serveurs/nas/installation.md](../../serveurs/nas/installation.md) §4

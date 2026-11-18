# NAS — état de la reconstruction

> Rôle : état constaté et étapes de remise en service du nouveau NAS.
> Mise à jour : 7 novembre 2026.
> Statut : retour au Pi 4 ; restauration préparée, exécution administrateur en attente.

| Élément | État |
|---|---|
| Matériel | Raspberry Pi 4 Model B Rev 1.5 confirmé en SSH ; Pi 5/HAT mis de côté après diagnostic PCIe |
| Système | Installation neuve Debian 13 Trixie 64 bits, sur SD de 119,1 Go |
| Réseau | 192.168.1.80 ; alias SSH `pinas` du PC corrigé et connexion par clé vérifiée |
| Sauvegarde Pi 4 | Archive de 186 313 887 octets retrouvée sur le PC ; lecture gzip et inventaire vérifiés, restauration à tester |
| Git / miroir GitHub | Quatre dépôts dans l'archive transférée ; restauration et comparaison GitHub encore à exécuter |
| Samba | Deux partages identifiés dans la sauvegarde : Oceane (oce) et antho (antho) ; base des mots de passe présente |
| NVMe | Aucun NVMe utilisé ; aucune opération de formatage réalisée par l'assistant |
| Administration | Socle Ansible préparé dans `infra/` ; contrôleur Linux et exécution sur NAS à valider |

L'installation historique de juillet dans `installation.md` décrit le Pi 4. Elle
sert de référence de récupération et ne prouve pas l'état du Pi 5.

La procédure générale est dans
[le guide d'administration](../../guides/administrer-homelab.md).
Ne réactiver le hook de miroir qu'après vérification des références restaurées.

## Restauration préparée sur le Pi 4

Le dossier privé `/home/pinas/nas-recovery/` contient l'archive et
`restore-nas-pi4.sh`, dont la syntaxe a été vérifiée. Le SHA256 de la copie sur
le Pi correspond à celui de l'archive du PC et son flux gzip est lisible.
Le système neuf a été contrôlé : `/srv` est vide, `pinas` conserve l'UID 1000,
les UID/GID nécessaires aux comptes restaurés sont disponibles.

Le script restaure sélectivement les données et comptes techniques, conserve
l'accès administrateur actuel et désactive les hooks de miroir. Il ne recopie
pas globalement `/etc`. Il refuse de remplacer un dossier `/srv/git` ou
`/srv/partages` existant. Son exécution et les essais fonctionnels restent à faire.

## Contrôle de l'archive

SHA256 relevé : `88a55cbf47c0d5796618d96c1b884103908d177c94b45f4fc2d7c694fa611d10`.
La comparaison à l'empreinte calculée sur l'ancien NAS n'a pas été refaite ici.
L'archive contient 3 055 entrées et quatre dépôts bare : `framework.git`,
`homelab.git`, `inference-au-harnais.git`, `memoire-agent.git`.
Les trois premiers contiennent un hook `post-receive` ; le quatrième n'en contient pas.
La présence des fichiers ne prouve pas encore l'intégrité Git ni le fonctionnement
des miroirs après restauration.

# Gestion du NAS

> Plan de mise en service et de remplacement du NAS. Mis à jour le 9 novembre 2026.
> État actuel. Un seul NAS sur Raspberry Pi 5 avec le compte `pinas`. Les quatre dépôts et les deux partages ont été restaurés sur le NVMe. Git répond via SSH depuis le PC admin, Samba est actif et l’administrateur confirme l’accès aux fichiers via SMB. Le registry reste à mettre en service.

## Stockage et reconstruction

Le système démarre sur microSD. Le NVMe Crucial est le disque de données, monté sur `/srv` par UUID. En cas de panne du Pi, on installe une microSD fraîche et on transfère le NVMe intact dans le Pi de remplacement. Le PC admin conserve une copie utilisable du dépôt Ansible, de l’inventaire et des secrets de récupération.

Montage confirmé en SSH sur le Pi. Le Crucial `CT1000P310SSD8` (série `25485499B748`) contient une partition `ext4` montée sur `/srv`, avec l’UUID `97498878-33ac-4e4b-bc8f-c6094172f15c`. La vérification de `/etc/fstab` a réussi.

| Emplacement | Contenu à conserver |
|---|---|
| `/srv/git` | Les quatre dépôts bare, leurs objets et leurs références. |
| `/srv/partages` | Les fichiers des partages `antho` et `Oceane`. |
| `/srv/samba` | L’état Samba à conserver, dont la base d’authentification et l’identité du serveur. Répertoires privés. |
| `/srv/appdata/registry` | Le stockage des images OCI publiées. Monté dans le conteneur sur le chemin prévu par sa configuration. |
| `/srv/appdata/<service>` | Les données persistantes des autres applications conteneurisées hébergées sur le NAS. |
| Support distinct du NVMe | Une sauvegarde versionnée des données et de l’état nécessaire à leur restauration. Les copies des services des tours arrivent sur le NAS puis sont incluses dans cette sauvegarde. |

Utiliser le [tutoriel de préparation du NVMe](preparer-nvme.md) pour ce disque qui contenait Windows. Lors d’un remplacement, le rôle Ansible monte le disque déjà préparé. Il contrôle le point de montage et l’UUID avant de créer des dossiers ou de lancer les services qui dépendent de `/srv`.

## Matrice des accès

**Dépôts Git** — `framework.git`, `homelab.git`, `inference-au-harnais.git` et `memoire-agent.git`.

| Entité | Identité | Ressource | Droits et protocole |
|---|---|---|---|
| Administrateur depuis le PC | `pinas` | Système du NAS et quatre dépôts | SSH par clé avec `sudo`. Lecture et écriture Git. |
| Antho depuis Windows | `antho` | Partage `antho` | Lecture et écriture SMB. Utiliser `\\nas\antho` si le nom `nas` résout sur le LAN. |
| Océane | `oce` | Partage `Oceane` | Lecture et écriture SMB. |
| Tour `lab-studio` | `agent0` sur le NAS | Les quatre dépôts | Lecture et écriture Git sur SSH avec sa propre clé et le groupe `agents`. Le login Linux sur la tour est `studio`. [Mise en service](../serveurs/lab-studio/renommer.md#créer-laccès-git-de-lab-studio-avec-agent0) |
| Tour `jarvis-core` | Compte SSH du NAS dédié à la tour, à confirmer | Les quatre dépôts | Lecture et écriture Git sur SSH avec sa propre clé. |
| Tous les agents | Identité SSH propre à chaque agent qui se connecte directement | `memoire-agent.git` | Lecture pour tous. Écriture pour les agents qui alimentent la mémoire. |
| PC admin ou machine de build désignée | Identité de publication dédiée | Registry privé | `pull` et `push` sur les dépôts d’images qu’elle publie. |
| Moteur Docker de `lab-studio` | `lab-studio`, compte du registry | Images du registry privé | `pull` via HTTPS sur le port 5001. |
| Autres hôtes qui déploient | Identité de lecture par hôte | Images requises par leurs projets Compose | `pull` via HTTPS une fois leurs comptes configurés. |
| Service de miroir Git, à activer plus tard | Identité de service dédiée | Les quatre dépôts et leurs miroirs GitHub privés | Lecture sur le NAS et écriture vers GitHub. Flux sortant. |

Les tours peuvent partager un groupe Git pour leurs droits actuels. Chaque tour garde sa clé pour permettre une révocation séparée. Un agent qui emprunte la clé d’une tour reçoit ses droits. Pour un accès limité à la mémoire, donner à l’agent sa propre clé et les droits associés sur ce dépôt.

Créer les comptes pendant la préparation, puis activer leurs accès dans l’ordre des tests. Recréer les comptes avec les mêmes UID/GID à chaque installation. Tester aussi les refus attendus, notamment entre les deux partages SMB et entre les identités de publication et de lecture du registry.

## Mise en service et restauration

1. Vérifier le modèle exact du HAT Seeed Studio, l’OS, le support de démarrage, la configuration PCIe qui fonctionne et le chemin du fichier de démarrage. Consigner ce profil avant de le reproduire. Les réglages diffèrent selon le HAT et le mode de démarrage. [Guide Seeed Studio](https://wiki.seeedstudio.com/raspberry_pi_5_uses_pcie_hat_dual_hat/)
2. Vérifier l’archive sur le PC admin avec `Get-FileHash -Algorithm SHA256`. Elle se trouve dans `C:\Users\antho\Sauvegardes\nas-rpi4-20261106-203458\nas-rpi4-backup.tar.gz`. Empreinte vérifiée lors du relevé précédent.

   ```text
   88a55cbf47c0d5796618d96c1b884103908d177c94b45f4fc2d7c694fa611d10
   ```

3. Vérifier le montage du NVMe par UUID. Le [script de restauration Pi 5](../infra/diagnostics/restore-nas-pi5.sh) prépare l’extraction dans un dossier privé sur le disque, contrôle les dépôts avec `git fsck --full` et restaure les dépôts, les partages et l’état Samba. Les hooks de miroir restent désactivés.
4. L’archive et le script ont été transférés dans `~/nas-recovery/` sur le Pi. L’empreinte de la copie et la syntaxe du script ont été vérifiées. Le 9 novembre, la restauration s’est terminée en mode `--resume` depuis `/srv/.restore-nas.ANtfWxwZ`, où la configuration Samba précédente est conservée. Les quatre dépôts répondent à `git ls-remote` depuis le PC admin. `smbd` est actif et le port 445 répond à `192.168.1.124`. Les hooks Git sont désactivés sur les quatre dépôts.
5. L’accès aux fichiers via SMB est confirmé par l’administrateur. Il reste à consigner le test d’écriture et le refus d’accès croisé pour chaque partage. Tester le clone des quatre dépôts, puis un push contrôlé avec chaque identité de tour une fois activée.
6. Mettre en service le registry et publier une première image. Vérifier depuis une tour qu’un `pull` fonctionne, qu’un `push` avec l’identité de lecture échoue et que l’image reste disponible après recréation du conteneur registry.
7. Faire un essai avec une seconde microSD. Rejouer Ansible avec le NVMe existant, puis tester SSH, Git, Samba et un `pull` sans cache local. Garder une copie à jour des données et des secrets sur un autre support pour le cas où le NVMe lui-même tombe en panne.

## Registry d’images

Le registry est un service Compose obligatoire du NAS. La cible proposée est CNCF Distribution, avec une image de démarrage ARM64 vérifiée et épinglée, un nom stable sur le LAN, TLS et authentification. Le stockage est monté depuis `/srv/appdata/registry`. Ansible installe Docker, déploie le Compose et distribue la confiance TLS et les identifiants aux hôtes concernés. Le mécanisme d’autorisation doit distinguer `pull` et `push`. Pour Distribution, prévoir un service de jetons avec des droits par dépôt. Son authentification `htpasswd` seule fournit une authentification commune. [Déploiement Distribution](https://distribution.github.io/distribution/about/deploying/) · [Droits des jetons](https://distribution.github.io/distribution/spec/auth/scope/) · [Certificats côté Docker](https://docs.docker.com/engine/security/certificates/)

**Le registry doit pouvoir démarrer avant les applications.** Son image, et celles de ses dépendances de démarrage, viennent d’une source externe épinglée ou d’une archive d’images accessible depuis le PC admin. Le dépôt d’infra, les paramètres TLS et les secrets nécessaires au démarrage sont récupérables sans le registry. Les identifiants et les clés privées restent dans un stockage privé hors Git.

Le PC admin ou une machine de build publie les images maison. Les images tierces des applications sont importées dans le registry avec leurs versions et les architectures nécessaires. Les Compose référencent les images du registry par digest. Ansible récupère les images sur l’hôte qui les exécutera. Pour revenir à une version précédente, conserver l’ancien digest, son image et une sauvegarde des données si la mise à jour change leur format. [Récupération d’une image par digest](https://docs.docker.com/reference/cli/docker/image/pull/)

La procédure de déploiement et le tableau des tâches se trouvent dans [Gestion Ansible](gestion-ansible.md).

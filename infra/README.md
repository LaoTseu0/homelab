# Administration du homelab

> Rôle : point d'entrée technique de la gestion Ansible.
> Mise à jour : 6 novembre 2026.
> Statut : socle préparé ; exécution Linux et validation sur les machines à faire.

Le guide opérateur est dans [guides/administrer-homelab.md](../guides/administrer-homelab.md).
La décision et les responsabilités sont décrites dans
[architecture/exploitation.md](../architecture/exploitation.md).

| Fichier/dossier | Responsabilité |
|---|---|
| `inventory.local.yml` | Adresses et paramètres réellement utilisés, copie locale ignorée par Git |
| `inventory.example.yml` | Exemple documenté des trois machines |
| `audit.yml` | Lecture de l'OS, des disques et des chemins de données |
| `site.yml` | Application de la configuration, une machine à la fois |
| `roles/base/` | Paquets communs et fuseau horaire |
| `roles/docker/` | Docker Engine et Compose via le dépôt officiel |
| `roles/nas/` | Git bare et Samba ; aucun formatage ni restauration automatique |
| `roles/jarvis/` | Prise en charge des fichiers Compose existants et du satellite déjà installé |
| `secrets/<machine>/` | Fichiers locaux sensibles, ignorés par Git |

## Ce qui reste à terminer

- Confirmer l'IP, l'OS et les disques du nouveau NAS, puis restaurer et vérifier les données.
- Mettre en place le contrôleur Linux avec mise ; WSL absent du PC à l'inventaire initial.
- Valider les playbooks avec Ansible et les exécuter sur le NAS.
- Automatiser le miroir GitHub après comparaison des références ; il n'est pas activé ici.
- Organiser le stockage NVMe et les sauvegardes sur un support distinct.
- Déployer le registry avec TLS, authentification et image ARM64 vérifiée.
- Relever les images réellement exécutées et épingler les versions du pipeline vocal.
- Préparer NVIDIA et le logiciel du satellite sur une machine vierge : le rôle Jarvis
  vérifie leurs prérequis mais ne les installe pas encore.
- Séparer ensuite la supervision du projet Jarvis et choisir le moteur de jarvis-core.

Les configurations Compose actuelles restent la source unique des définitions de
conteneurs. L'ancien installateur est conservé pendant la migration ; une fois un
service pris en charge par Ansible, ne plus alterner avec cet installateur.

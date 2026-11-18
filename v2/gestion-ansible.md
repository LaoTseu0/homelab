# Gestion Ansible

> Plan de reconstruction et de mise à jour des hôtes. Mis à jour le 9 novembre 2026.
> Le socle existe dans `infra/`. Les rôles de stockage, de registry et de reprise complète décrits ici restent à implémenter et à valider.

## Qui gère quoi

| Outil | Responsabilité |
|---|---|
| Ansible | Configure les hôtes par SSH. Gère le profil du HAT, les montages, les comptes et leurs UID/GID, les clés, Git, Samba, Docker, les certificats et le lancement des projets Compose. |
| Docker Compose | Décrit les applications conteneurisées, leurs images, leurs réseaux, leurs montages et leurs contrôles de santé. Un projet est appliqué sur l’hôte qui exécute ses services. |
| Docker et registry privé | Construisent ou importent les images, les publient et les distribuent aux hôtes qui en ont besoin. |
| Outil de sauvegarde et systemd | Sauvegardent et planifient les copies des données persistantes sur un support distinct. |
| Git | Conserve la configuration, les versions d’images et la procédure. Le PC admin garde une copie utilisable pendant une panne du NAS. |

Le NAS garde Git via OpenSSH et Samba comme services système gérés par Ansible. Le registry et les applications sont déployés avec Compose. Les fichiers de déploiement restent près des services dans `deploiement/`. La tour qui héberge les services Jarvis est déclarée comme `lab-studio` dans Ansible, avec le login Linux `studio`. [Procédure de bascule](../serveurs/lab-studio/renommer.md)

## Tableau des tâches

| Ordre | Travail | Outil et validation |
|---|---|---|
| 1 | Relever l’état du Pi 5, du HAT et du NVMe. Vérifier l’archive NAS du PC et faire une extraction d’essai. | **SSH et outils système**, puis audit Ansible. Identifier le disque par modèle et série. Contrôler les dépôts, les partages et les comptes restaurables. |
| 2 | Effacer le NVMe issu du PC Windows, créer le système de fichiers et monter `/srv`. | **Opération manuelle unique** selon le [tutoriel NVMe](preparer-nvme.md). Vérifier l’UUID et le montage après redémarrage. |
| 3 | Restaurer Git et SMB sur le Pi 5. Recréer les propriétaires, préparer les comptes techniques et tester les accès par lots. | **Script de restauration adapté** pour les données. **Ansible** pour les paquets, le montage, les comptes, les clés et Samba. Consulter la [matrice d’accès](gestion-nas.md#matrice-des-accès). |
| 4 | Préparer le contrôleur et rendre le socle du NAS rejouable. | **Linux, mise et Ansible** sur le PC admin. Ajouter les tâches manquantes dans `infra/`. Valider sur le Pi 5 et contrôler un deuxième passage. |
| 5 | Démarrer le registry avec stockage sur le NVMe, TLS et droits de lecture et de publication distincts. | **Ansible** pour Docker, la confiance TLS et les accès. **Compose** pour le registry et son autorisation. Tester la persistance et un `pull` depuis une tour. |
| 6 | Publier la première image et préparer les références des autres applications. | **Docker** pour construire ou importer les images. Publier dans le registry, vérifier les architectures, puis enregistrer les digests dans les Compose. Commencer par `jarvis-exporter`. |
| 7 | Mettre en place les sauvegardes et tester la reconstruction sur une microSD fraîche. | **Outil de sauvegarde, timer systemd et Ansible**. Refaire le socle à partir du PC, remonter le même NVMe et tester SMB, Git et le registry. |
| 8 | Cartographier les flux et reprendre les services existants par lots, en commençant par la supervision. | **Audit SSH/Compose**, puis **Compose** pour Prometheus et Grafana. Comparer cibles, règles, dashboards et volumes. **Ansible** applique les règles réseau après validation. |
| 9 | Reprendre les applications de `lab-studio`, puis intégrer l’inférence sur `jarvis-core`. | **Ansible** pour les noms, comptes, pilotes et prérequis GPU. **Compose** pour les applications. Sauvegarder Home Assistant et valider le texte, la voix et les métriques après migration. |
| 10 | Activer le miroir des quatre dépôts Git. | **Git et service systemd** sous une identité dédiée, déployés par **Ansible**. Examiner les divergences et la confidentialité de l’historique avant le premier envoi vers GitHub. |

## Contrôleur et vérifications

Utiliser un contrôleur Linux accessible depuis le PC admin, par exemple WSL si le PC est sous Windows. Installer mise dans cet environnement et utiliser les versions du projet. Depuis `infra/` dans la copie Linux du dépôt, valider les outils avant d’installer les dépendances.

```bash
mise trust
mise install
mise current
mise which python
mise exec -- python -m venv .venv
mise exec -- .venv/bin/python -m pip install -r requirements-controller.txt
mise exec -- .venv/bin/ansible-galaxy collection install -r requirements.yml -p .collections
```

Créer `inventory.local.yml` à partir de `inventory.example.yml` en renseignant les adresses et clés réelles. Déclarer l’UUID du NVMe et les UID/GID avec le futur rôle de stockage et de comptes. Vérifier l’empreinte SSH du Pi avant d’accepter sa clé. Les clés privées et secrets restent dans un emplacement privé récupérable depuis le PC admin.

```bash
mise exec -- .venv/bin/ansible-inventory --graph
mise exec -- .venv/bin/ansible-playbook audit.yml --limit nas
mise exec -- .venv/bin/ansible-playbook site.yml --syntax-check
```

L’audit actuel relève l’OS, les disques, les versions Docker et quelques chemins. Compléter ses résultats avec les services et flux réellement actifs. Une fois le nouveau rôle NAS validé, examiner `site.yml --limit nas --check --diff` avant l’application. Le mode `--check` reste partiel sur une machine vierge. Masquer les tâches contenant des secrets. Références du socle actuel. [Documentation `infra/`](../infra/README.md) · [Audit](../infra/audit.yml)

## Ordre de rejeu sur une infrastructure neuve

1. Préparer l’OS et l’accès SSH des hôtes. Sur le NAS, appliquer le profil Seeed vérifié, redémarrer si nécessaire et monter `/srv` par UUID. Vérifier le montage avant les services et les écritures. Récupérer le contenu depuis la sauvegarde si le NVMe est neuf.
2. Recréer les comptes et l’état des services système. Démarrer Git et Samba sur les données existantes. Installer Docker et démarrer le registry depuis son image de démarrage accessible indépendamment du registry.
3. Tester le registry et ses droits depuis un autre hôte. Configurer sur chaque hôte Docker la confiance TLS et les identifiants de l’utilisateur qui exécute effectivement Compose. Démarrer ensuite les projets applicatifs de cet hôte avec leurs montages et secrets.
4. Vérifier la santé des services et le résultat métier. Tester Git, les partages, la restauration des données et le téléchargement d’une image depuis une machine sans cache. La restauration d’une sauvegarde reste une opération explicite et séparée du rejeu normal.

## Mise à jour d’une application

1. Construire l’image maison ou importer la version tierce validée. Publier dans le registry privé et relever le digest utilisable sur l’architecture cible.
2. Modifier la référence d’image du service dans Git. Sauvegarder les données avant une mise à jour qui les migre. Garder l’image et la référence précédentes disponibles.
3. Appliquer Ansible sur un hôte à la fois. Le rôle utilise `community.docker.docker_compose_v2` pour récupérer les images du projet et appliquer la définition Compose. Vérifier l’état et la fonction du service après recréation. [Module Compose v2](https://docs.ansible.com/projects/ansible/latest/collections/community/docker/docker_compose_v2_module.html)
4. En cas d’échec, remettre la référence précédente et rejouer le déploiement. Si le format des données a changé, restaurer la sauvegarde compatible avec cette version avant de remettre le service en route.

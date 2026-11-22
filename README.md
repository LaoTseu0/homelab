# Homelab

Le homelab s’administre depuis le PC Windows. Ubuntu sous WSL exécute Ansible et se connecte aux machines Linux par SSH. Ansible configure les hôtes et déploie les services Docker Compose.

| Pour retrouver… | Ouvrir |
|---|---|
| Les équipements et leurs branchements Ethernet, Wi-Fi et USB | [Topologie physique](doc/architecture/topologie-physique.md) |
| Les sous-réseaux et les échanges entre services | [Topologie logique](doc/architecture/topologie-logique.md) |
| Les adresses IP, les ports et les accès Samba | [Réseau](doc/architecture/reseau.md) |
| Le matériel, les systèmes et les relevés à compléter | [Machines](doc/architecture/machines.md) |
| Les dossiers de données, le montage du NVMe et leur gestion | [Volumes](doc/architecture/volumes.md) |
| Les commandes de déploiement | [Déployer](doc/exploitation/deployer.md) |
| La publication d’une image et la remise en service | [Publier une image](doc/exploitation/publier-une-image.md) · [Remettre le NAS en service](doc/exploitation/remettre-le-nas-en-service.md) |
| Les choix techniques et les pistes d’évolution | [Sommaire complet de la documentation](doc/README.md) |

La configuration déployable se trouve dans [`ansible/`](ansible/). L’[inventaire](ansible/inventory.yml) indique les cibles SSH, [`group_vars/`](ansible/group_vars/) et [`host_vars/`](ansible/host_vars/) contiennent leurs variables. [`roles/`](ansible/roles/) rassemble des rôles réutilisables, un par fonction (Samba, Docker, Ollama…), et chaque playbook `configurer-*.yml` est le profil d’une machine : la liste des rôles qu’elle reçoit.

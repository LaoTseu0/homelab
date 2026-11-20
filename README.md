# Homelab

Le homelab s’administre depuis le PC Windows. Ubuntu sous WSL exécute Ansible et se connecte aux machines Linux par SSH. Ansible configure les hôtes et déploie les services Docker Compose.

| Pour retrouver… | Ouvrir |
|---|---|
| Les équipements et leurs branchements Ethernet, Wi-Fi et USB | [Topologie physique](doc/topologie-physique.md) |
| Les sous-réseaux et les échanges entre services | [Topologie logique](doc/topologie-logique.md) |
| Les adresses IP, les ports et les accès Samba | [Réseau](doc/reseau.md) |
| Le matériel, les systèmes et les relevés à compléter | [Machines](doc/machines.md) |
| Les dossiers de données, le montage du NVMe et leur gestion | [Volumes](doc/volumes.md) |
| Les commandes de déploiement, les accès et la remise en service | [Exploitation](doc/exploitation.md) |

La configuration déployable se trouve dans [`ansible/`](ansible/). L’[inventaire](ansible/inventory.yml) indique les cibles SSH, [`host_vars/`](ansible/host_vars/) contient leurs variables, et [`roles/`](ansible/roles/) rassemble les tâches et les fichiers qu’elles déploient. Les fichiers Compose de la tour se trouvent dans le [rôle lab-studio](ansible/roles/lab-studio/).

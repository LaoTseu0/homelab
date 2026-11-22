# Projet : machines virtuelles

Ce document explique pourquoi l’infrastructure actuelle n’utilise pas de VM pour ses services, ce qu’elles apporteraient et comment les introduire. Rien n’est encore mis en œuvre. Le poste d’administration utilise déjà une VM légère : WSL 2, qui exécute Ansible.

## VM et conteneur

- **Une VM** simule une machine complète, avec son propre noyau et son OS. L’isolation est forte, au prix de RAM, de disque et d’un système de plus à maintenir.
- **Un conteneur** est un processus isolé qui partage le noyau de l’hôte. Il est léger et démarre vite, mais son isolation est plus faible.

Les deux se combinent : en entreprise, des conteneurs tournent très souvent dans des VM.

## Pourquoi les services tournent sans VM

| Machine | VM utile ? | Raison |
|---|---|---|
| NAS (Pi 5) | Non | Ressources limitées ; Samba, Git et le registry ont besoin d’un accès direct au NVMe |
| Passerelle (Pi 4) | Non | Un seul rôle réseau, simple et léger |
| `lab-studio` | Pas pour la production | Le GPU de 6 Gio ne se donne qu’à une seule VM à la fois (passthrough), et le micro USB devrait aussi être transmis |

Les services sont liés au matériel : GPU, NVMe et USB. Ils s’exécutent donc en conteneurs directement sur l’hôte, et Ansible permet de reconstruire les machines.

## Ce que les VM apporteraient

1. **Un environnement de recette.** Le `--check --diff` est aujourd’hui la seule répétition avant de toucher aux vraies machines. Une VM permet de jouer réellement un playbook, de casser et de recommencer.
2. **Des snapshots.** Ils permettent de revenir en arrière après une migration ratée. Un snapshot n’est pas une sauvegarde : il disparaît avec le disque.
3. **Un test depuis zéro.** Appliquer `site.yml` sur une VM neuve prouve que l’infrastructure est réellement reproductible.
4. **Une meilleure isolation.** Home Assistant tourne en `privileged: true` : s’il est compromis, l’attaquant est pratiquement root sur la tour. Une VM contiendrait les dégâts. C’est aussi l’approche à retenir pour un futur service exposé à Internet, comme la [messagerie](messagerie.md).

Les coûts : RAM et disque réservés, un OS de plus à mettre à jour par VM et une couche supplémentaire à administrer.

## Cible proposée

Garder la production telle quelle et installer **Proxmox sur la seconde tour**, si son matériel s’y prête. Ses caractéristiques restent à relever dans [Machines](../architecture/machines.md).

| VM | Rôle | Limite |
|---|---|---|
| Ubuntu | Imiter `lab-studio` | Sans GPU : `nvidia_gpu` et `ollama` ne sont pas testables tels quels |
| Debian | Imiter le NAS | Architecture `x86_64` au lieu d’ARM, sans le rôle `rpi_boot` |
| 3 petites VM | Cluster k3s d’apprentissage | Séparé de la production |

## Étapes

1. Mettre en place la **sauvegarde** des données réelles : c’est le seul de ces sujets qui les protège.
2. Relever le matériel de la seconde tour et installer Proxmox.
3. Ajouter un **inventaire de recette**, distinct de l’inventaire réel.
4. Créer une VM neuve et y appliquer les profils pour vérifier la reproductibilité.
5. Faire passer chaque changement important par la recette avant la production.
6. Brancher cette recette sur le futur [pipeline CI/CD](pipeline-ci-cd.md).
7. Monter ensuite le cluster k3s d’apprentissage.

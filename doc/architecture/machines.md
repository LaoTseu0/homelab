# Machines

Relevé consolidé le 19 novembre 2026, complété le 28 novembre pour `lab-forge`. Les caractéristiques ci-dessous proviennent de relevés système, de tests réalisés dans le lab ou de la configuration Ansible en vigueur. Les valeurs marquées **à relever** restent à confirmer sur le matériel. Pour l’adressage et les ports, voir [Réseau](reseau.md).

## PC admin — `DESKTOP-61C28MN`

Relevé effectué directement sous Windows le 19 novembre 2026.

| Élément | Relevé |
|---|---|
| Ordinateur et carte mère | ASUS TUF Gaming F17 `FX707ZU4_TUF707ZU4`, carte mère ASUSTeK `FX707ZU4` |
| Firmware | UEFI/BIOS `FX707ZU4.329` |
| Processeur | Intel Core i7-12700H de 12e génération, 14 cœurs et 20 processeurs logiques |
| RAM | 1 module Samsung `M471A2K43EB1-CWE`, 16 Gio, vitesse configurée de 3 200 MT/s |
| GPU | Intel UHD Graphics, pilote `32.0.101.6790`. NVIDIA GeForce RTX 4050 Laptop GPU, 6 141 Mio visibles, pilote `610.88` |
| Stockage | SSD NVMe Micron 2400 `MTFDKBA512QFM`, 512 110 190 592 octets (~477 Gio) |
| Interfaces réseau | Realtek PCIe GbE Family Controller, Intel Wi-Fi 6 AX201 160 MHz |
| Système | Windows 11 Famille x64, version système `10.0.26200` |
| Control node | Ubuntu sous WSL 2. [Versions et installation de Python et Ansible](../exploitation/deployer.md#depuis-le-pc-admin) |

## NAS — `nas`

| Élément | Relevé |
|---|---|
| Carte et architecture | Raspberry Pi 5, ARM64. Révision, RAM réelle et version EEPROM à relever |
| Démarrage | microSD `/dev/mmcblk0` de 119,1 Gio visibles. `mmcblk0p1` monte `/boot/firmware`, `mmcblk0p2` porte la racine ext4 |
| Stockage de données | Crucial P310 `CT1000P310SSD8`, 1 To nominal, 931,5 Gio visibles. Une partition GPT en ext4 montée sur `/srv`. Montage et contenu dans [Volumes](volumes.md) |
| Contrôleur de stockage | HAT PCIe/NVMe Seeed Studio. Modèle exact, réglages PCIe et liaison négociée à relever |
| Châssis et alimentation | Boîtier, refroidissement, bloc d’alimentation et modèle microSD à relever |
| Système | Raspberry Pi OS 64 bits, base Debian Trixie. Version du noyau à relever |
| Moteur de conteneurs | Docker Engine `29.10.0`, Compose `v5.8.0`, stockage `overlayfs` au dernier relevé. Les contrôleurs mémoire et swap ont été vérifiés actifs ensuite |
| Rôle | L’état du homelab, dont le second cerveau versionné dans Git. Voir la [décision 002](../decisions/002-repartition-des-roles.md) |
| Services | Samba et Git sur l’hôte. Registry Distribution conteneurisé. Rôles appliqués dans le [profil du NAS](../../ansible/configurer-nas.yml), réglages dans les [variables NAS](../../ansible/host_vars/nas/main.yml) |

## Passerelle — `lab-rpi4-1`

| Élément | Relevé |
|---|---|
| Carte | Raspberry Pi 4 Model B. Révision et RAM à confirmer sur la passerelle |
| Réseau | Wi-Fi intégré côté Bbox, Ethernet côté Homelab |
| Services | NetworkManager pour la passerelle et HAProxy pour le relais SMB |
| À relever | Révision de la carte, RAM, support et capacité de démarrage, OS, noyau, EEPROM, alimentation et refroidissement |

## Tour — `lab-studio`

| Élément | Relevé |
|---|---|
| Rôle | Orchestration, toujours allumée : harness (cible), Home Assistant et petit modèle sur la 2060. Voir la [décision 002](../decisions/002-repartition-des-roles.md) |
| Système | Ubuntu 26.04, x86-64. Noyau `7.0.0-42-generic` observé au rétablissement d’Ollama |
| GPU | NVIDIA GeForce RTX 2060 Rev. A, TU106, ID PCI `10de:1f08`, 6 144 Mio. Pilote `595.99.02` et branche Ubuntu `595-open` validés le 18 novembre |
| Périphérique audio | ReSpeaker XVF3800 en USB, actuellement débranché. L’unité `wyoming-satellite` est gérée par Ansible |
| Services | Home Assistant, Ollama, Whisper, Piper et openWakeWord |
| À relever | Modèle CPU exact, RAM et références des modules, carte mère, BIOS, stockage, contrôleur Ethernet, alimentation, boîtier, refroidissement et versions Docker/Compose |

## Seconde tour — `lab-forge`

Anciennement `jarvis-core`. Ubuntu Server a été réinstallé le 28 novembre 2026, et le relevé a été fait le même jour par SSH, avec sudo. La tour est dans l’[inventaire Ansible](../../ansible/inventory.yml), sans profil `configurer-*.yml` pour l’instant : aucun rôle ne lui est encore appliqué.

| Élément | Relevé |
|---|---|
| Rôle | Calcul sans état : moteur LLM pour les gros modèles et essais de modèles. Voir la [décision 002](../decisions/002-repartition-des-roles.md) |
| Carte mère et firmware | MSI MAG B650 TOMAHAWK WIFI (`MS-7D75`) rév. 1.0, firmware `1.Q0` du 19 mai 2026 |
| Processeur | AMD Ryzen 9 7900X, 12 cœurs et 24 threads. Virtualisation AMD-V disponible |
| RAM | 64 Go en 2 × 32 Go DDR5 Corsair `CMH64GX5M2B6000Z30`, à 6 000 MT/s configurés. 60 Gio visibles. Swap de 8 Gio |
| GPU | NVIDIA GeForce RTX 4090 (AD102) en `01:00.0`, sans pilote installé. iGPU AMD Raphael en `10:00.0` pour la console |
| IOMMU | AMD-Vi détecté au démarrage. Groupes IOMMU à vérifier avant un passthrough avec `ls /sys/kernel/iommu_groups` |
| Stockage | NVMe WD_BLACK SN850X HS 4 To : `/boot/efi` (1 Gio), `/boot` (2 Gio) et un PV LVM `ubuntu-vg` de 3,6 Tio. Seul `ubuntu-lv` existe : 100 Gio sur `/`, 12 Gio utilisés. Le reste du VG est libre pour de futurs volumes. Pas de chiffrement |
| Contrôleurs | Deux contrôleurs SATA : AMD 600 Series et ASMedia ASM1061/1062. Aucun disque SATA branché |
| Interfaces réseau | Realtek RTL8125 2.5GbE `enp12s0`, active. Wi-Fi `wlp13s0`, inactive |
| Système | Ubuntu Server 26.04.1 LTS, x86-64, noyau `7.0.0-44-generic`. Réseau géré par systemd-networkd. Snaps de base seulement (`core24`, `snapd`, `hwctl`) |
| Services | Installation de base : SSH, chrony, cron, fwupd, unattended-upgrades. Ni Docker ni service applicatif |
| Accès | Compte `forge`, membre du groupe `sudo`. Clés SSH distinctes pour Windows et WSL, alias `lab-forge` des deux côtés. L’authentification SSH par mot de passe est encore active : voir [Sécurité](../exploitation/securite.md#état-des-machines) |
| À relever | Alimentation, boîtier et refroidissement |

## Équipements réseau

| Équipement | État relevé |
|---|---|
| Bbox | Routeur du réseau Maison. Modèle exact et firmware à relever |
| TP-Link TL-SG108PE | Switch Ethernet du Homelab. Interface d’administration probablement en `192.168.50.232`, à confirmer. Révision matérielle et firmware à relever |

## Compléter les relevés

Depuis le dossier Ansible sous WSL, lancer `ansible-playbook -i inventory.yml diagnostics/inventorier.yml --ask-vault-pass`. Le playbook relève la distribution, le noyau, le CPU, la RAM visible, les disques, les interfaces et les composants PCI/USB détectés. Il utilise les accès SSH existants. Les références de l’alimentation, du HAT et du refroidissement se vérifient sur les étiquettes ou les composants.
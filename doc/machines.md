# Machines

Relevé consolidé le 19 novembre 2026. Les caractéristiques ci-dessous proviennent de relevés système, de tests réalisés dans le lab ou de la configuration Ansible en vigueur. Les valeurs marquées **à relever** restent à confirmer sur le matériel. Pour l’adressage et les ports, voir [Réseau](reseau.md).

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
| Control node | Ubuntu sous WSL 2. [Versions et installation de Python et Ansible](exploitation.md#depuis-le-pc-admin) |

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
| Services | Samba et Git sur l’hôte. Registry Distribution conteneurisé. Rôles appliqués dans le [profil du NAS](../ansible/configurer-nas.yml), réglages dans les [variables NAS](../ansible/host_vars/nas/main.yml) |

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
| Système | Ubuntu 26.04, x86-64. Noyau `7.0.0-42-generic` observé au rétablissement d’Ollama |
| GPU | NVIDIA GeForce RTX 2060 Rev. A, TU106, ID PCI `10de:1f08`, 6 144 Mio. Pilote `595.99.02` et branche Ubuntu `595-open` validés le 18 novembre |
| Périphérique audio | ReSpeaker XVF3800 en USB, actuellement débranché. L’unité `wyoming-satellite` est gérée par Ansible |
| Services | Home Assistant, Ollama, Whisper, Piper et openWakeWord |
| À relever | Modèle CPU exact, RAM et références des modules, carte mère, BIOS, stockage, contrôleur Ethernet, alimentation, boîtier, refroidissement et versions Docker/Compose |

## Seconde tour — `jarvis-core`

Le raccordement au Homelab et l’état de la tour depuis la bascule réseau restent à vérifier. Le relevé doit couvrir le nom système, l’OS, la carte mère et le firmware, le CPU, la RAM par module, les GPU et leur VRAM, les disques et leurs contrôleurs, les interfaces réseau, l’alimentation, le refroidissement et les services actifs.

## Équipements réseau

| Équipement | État relevé |
|---|---|
| Bbox | Routeur du réseau Maison. Modèle exact et firmware à relever |
| TP-Link TL-SG108PE | Switch Ethernet du Homelab. Révision matérielle et firmware à relever |

## Compléter les relevés

Depuis le dossier Ansible sous WSL, lancer `ansible-playbook -i inventory.yml diagnostics/inventorier.yml --ask-vault-pass`. Le playbook relève la distribution, le noyau, le CPU, la RAM visible, les disques, les interfaces et les composants PCI/USB détectés. Il utilise les accès SSH existants. Les références de l’alimentation, du HAT et du refroidissement se vérifient sur les étiquettes ou les composants. La seconde tour pourra être relevée une fois son accès SSH établi.

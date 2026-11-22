# Réseau

Les schémas des branchements et des échanges sont dans [Topologie physique](topologie-physique.md) et [Topologie logique](topologie-logique.md).

## Adressage

La Bbox fournit l’accès Internet et le DHCP côté Maison. Le profil NetworkManager `homelab-lan` du Pi 4 utilise `ipv4.method shared` sur `eth0`. Le Pi 4 fournit le DHCP, le relais DNS et le NAT IPv4 côté Homelab. Les échanges entre les machines du Homelab passent directement par le switch.

| Machine | Interface | Adresse | Attribution |
|---|---|---|---|
| Pi 4 | `wlan0` | `192.168.1.84` | Dernier bail Bbox observé |
| Pi 4 | `eth0` | `192.168.50.1/24` | IP fixe |
| NAS | Ethernet | `192.168.50.198` | Dernier bail Homelab observé |
| PC admin | Ethernet | `192.168.50.68` | Dernier bail Homelab observé |
| `lab-studio` | `enp4s0` | `192.168.50.252` | Dernier bail Homelab observé |
| `jarvis-core` | À relever | À relever | Raccordement après la bascule à confirmer |

Les réservations DHCP restent à confirmer. Les adresses du NAS et du Pi 4 côté Maison sont utilisées par le relais SMB. L’adresse du NAS est également utilisée par le registry et son certificat. Si elle change, les configurations concernées doivent suivre. [Variables HAProxy](../../ansible/host_vars/lab-1.yml) · [Variables NAS](../../ansible/host_vars/nas/main.yml) · [Inventaire Ansible](../../ansible/inventory.yml)

## Flux

| Destination | Port | Usage et accès |
|---|---|---|
| Pi 4, LAN | 22/TCP | Administration depuis le PC admin via l’alias SSH `lab-1` |
| Pi 4, LAN | 67/UDP, 53/UDP et TCP | DHCP et relais DNS pour le Homelab |
| Pi 4, côté Bbox | 445/TCP | HAProxy filtre les deux IP source autorisées puis transmet au NAS |
| NAS | 22/TCP | Administration via l’alias SSH `pinas` et accès Git de `lab-studio` via `agent0` |
| NAS | 445/TCP | Samba. Accès direct depuis le PC admin, accès des téléphones via le Pi 4 |
| NAS | 5000/TCP, TLS | Registry de publication. Le compte `publisher` peut publier et lire les images |
| NAS | 5001/TCP, TLS | Registry de téléchargement. Lecture confirmée depuis `lab-studio` |
| `lab-studio` | 22/TCP | Administration SSH depuis le PC admin |
| `lab-studio` | 8123/TCP | Interface Home Assistant. Accès depuis le PC admin via `http://192.168.50.252:8123` |
| `lab-studio` | 11434/TCP | API Ollama, publiée par Compose |
| `lab-studio` | 10200, 10300, 10400/TCP | Piper, Whisper et openWakeWord, publiés par Compose |

Ce tableau décrit les flux configurés et les accès confirmés. Les ports publiés par Compose ne prouvent pas la présence de restrictions par IP. Le satellite audio est actuellement à l’arrêt. Compose de la tour : [Ollama](../../ansible/roles/ollama/templates/compose.yml.j2) · [Home Assistant](../../ansible/roles/home_assistant/templates/compose.yml.j2)

### Accès Samba via le relais

| Téléphone | IP Maison autorisée | Adresse SMB | Compte Samba |
|---|---|---|---|
| Antho | `192.168.1.101` | `smb://192.168.1.84/antho` | `antho` |
| Océane | `192.168.1.127` | `smb://192.168.1.84/Oceane` | `oce` |

Samba vérifie les comptes et les droits sur les partages. Depuis Windows sur le réseau Homelab, l’accès direct à `\\192.168.50.198\antho` est confirmé. L’écoute du relais a été vérifiée. Les tests d’ouverture depuis les deux téléphones et de refus depuis un troisième appareil restent à consigner.

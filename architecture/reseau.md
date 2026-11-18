# Architecture — réseau domestique

> Topologie du réseau local, adressage des machines et matrice des services.
> **Référence unique pour les IP** : toute doc ou config qui a besoin d'une
> adresse pointe ici — on ne duplique pas les IP au fil des documents.
> Dernière mise à jour — 15 novembre 2026.
> Statut — sous-réseau Homelab en service. Relais SMB actif côté Maison.

---

## 1. Vue d'ensemble

- La **Bbox** fournit Internet et DHCP au réseau Maison `192.168.1.0/24`.
- Le **Pi 4** rejoint directement la Bbox en Wi-Fi 5 GHz sur `wlan0`. Sur
  `eth0`, le profil NetworkManager `homelab-lan` fournit le DHCP, le relais
  DNS et le NAT IPv4 au réseau Homelab `192.168.50.0/24`.
- Le **TP-Link TL-SG108PE** relie le Pi 4, le NAS et le PC admin en Ethernet.
  Le NAS et le PC admin échangent directement sur le switch.
- Aucune redirection de port depuis Internet n'est documentée.
  [Politique de sécurité](securite.md)

```
Internet
└── Bbox — 192.168.1.254 — réseau Maison 192.168.1.0/24
    ├── Wi-Fi Maison → PC d’Océane et téléphones
    └── Wi-Fi 5 GHz → Pi 4, wlan0 — 192.168.1.84 (bail observé)
        └── Pi 4, eth0 — 192.168.50.1/24 (fixe)
            └── TP-Link TL-SG108PE — réseau Homelab 192.168.50.0/24
                ├── NAS Pi 5 — 192.168.50.198
                └── PC admin — 192.168.50.68
```

---

## 2. Adressage des machines

| Machine | Hostname | IP | Connexion | Adressage |
|---|---|---|---|---|
| Bbox | — | `192.168.1.254` | Réseau Maison | Passerelle Maison |
| Pi 4 | `lab-rpi4-1` | WAN `192.168.1.84`, LAN `192.168.50.1` | `wlan0` vers la Bbox, `eth0` vers le TP-Link | Bail Bbox côté WAN, IP fixe côté LAN |
| NAS (Pi 5) | `nas` | `192.168.50.198` | Ethernet via TP-Link | Bail DHCP du Pi 4 |
| PC admin | `DESKTOP-61C28MN` | `192.168.50.68` | Ethernet via TP-Link | Bail DHCP du Pi 4 |
| Serveur Jarvis | `lab-studio` | `192.168.50.252` | `enp4s0` via TP-Link | Bail DHCP du Pi 4 observé |
| Tour d'inférence LLM | `jarvis-core` | À confirmer (ancienne IP `192.168.1.187`) | À confirmer après la bascule | À confirmer |
| Satellites (futurs) | — | — | Wi-Fi | À réserver à l'ajout |

Les adresses issues des baux DHCP sont celles du dernier relevé. Elles peuvent
changer lors d'un renouvellement. Le DHCP côté Homelab est géré par le Pi 4.

## 3. Résolution de noms — convention

- **Machine → machine (configs, scripts, services)** : utiliser l'**IP**.
  Le mDNS (`.local`) dépend d'Avahi/systemd-resolved et peut échouer
  silencieusement entre serveurs headless — une config de service ne doit
  pas dépendre d'un mécanisme fragile.
- **Humain → machine (confort au quotidien)** : les alias
  `~/.ssh/config` restent très bien depuis le PC.
- L'alias SSH `pinas` doit pointer vers `192.168.50.198` dans les configurations
  Windows et WSL.
- Le Pi 4 est joignable en SSH avec le compte `lab-1` à `192.168.50.1`.
  L'accès avec la clé Windows dédiée `id_ed25519_lab1` a été vérifié.

## 4. Matrice des services (qui écoute où)

| Machine        | Port                  | Service                                                                     | Clients légitimes                              |
| -------------- | --------------------- | --------------------------------------------------------------------------- | ---------------------------------------------- |
| `lab-rpi4-1`   | 22/TCP                | SSH admin                                                                   | PC admin sur le réseau Homelab                 |
| `lab-rpi4-1`   | 67/UDP, 53/UDP+TCP    | DHCP et relais DNS sur `eth0`                                               | Clients du réseau Homelab                      |
| `lab-rpi4-1`   | 445/TCP               | HAProxy sur `192.168.1.84` vers `192.168.50.198:445`                          | Téléphones à `192.168.1.101` et `192.168.1.127` |
| nas            | 22/TCP                | SSH (Git + admin)                                                           | PC admin confirmé, accès Jarvis à revérifier   |
| nas            | 445/TCP               | SMB (partages `Oceane` et `antho`)                                          | Accès à `antho` confirmé depuis le PC admin    |
| jarvis-core    | 22                    | SSH admin                                                                   | pc-admin                                       |
| jarvis-core    | *(prévu)*             | API d'inférence LLM — port à définir (voir [inference.md](inference.md) §6) | lab-studio uniquement                      |
| lab-studio | 22                    | SSH admin                                                                   | pc-admin                                       |
| lab-studio | 8123                  | Home Assistant (web)                                                        | pc-admin / téléphones de la famille            |
| lab-studio | 11434                 | API Ollama (Qwen3 4B, voix)                                                 | local uniquement (HA, future couche agentique) |
| lab-studio | 10200 / 10300 / 10400 | Wyoming (piper / whisper / openwakeword)                                    | local uniquement (HA, satellite)               |
| lab-studio | 10700                 | wyoming-satellite « bureau »                                                | local uniquement (HA)                          |

Depuis le Wi-Fi Bbox, HAProxy filtre les adresses source. Samba vérifie
ensuite le compte et les droits du partage sur le NAS.

| Téléphone | IP source | Adresse dans l'appli SMB | Compte Samba |
|---|---|---|---|
| Antho | `192.168.1.101` | `smb://192.168.1.84/antho` | `antho` |
| Océane | `192.168.1.127` | `smb://192.168.1.84/Oceane` | `oce` |

Le service HAProxy est actif et activé au démarrage. Son écoute sur
`192.168.1.84:445` a été vérifiée. Il reste à consigner l'ouverture des
partages sur les deux téléphones et le refus depuis une autre IP Maison.

Les ports Jarvis décrivent la configuration documentée avant la bascule.
Leur joignabilité reste à vérifier sur le nouveau réseau.

> Sens du flux LLM : `lab-studio` est **cliente** de la future API de
> `jarvis-core` (le moteur), jamais l'inverse — voir [inference.md](inference.md) §3.

> Les ports « local uniquement » écoutent sur toutes les interfaces dans la
> configuration Jarvis documentée. Cette matrice sert de base aux futures
> règles UFW. [Politique de sécurité](securite.md)

## 5. Évolutions prévues (backlog)

- Réserver les adresses du NAS, du PC admin et de `lab-studio` sur le
  DHCP du Pi 4. Relever l’IP de `jarvis-core` après raccordement.
- Réserver côté Bbox le bail Wi-Fi du Pi 4 et ceux des deux téléphones.
  Le relais HAProxy dépend de ces adresses et de celle du NAS.
- Wake-on-LAN de `jarvis-core` depuis `lab-studio` — si la politique
  d'alimentation retenue est « à la demande » ([inference.md](inference.md) §6).
- Fiabiliser le lien RDC↔étage (Ethernet/CPL à terme).
- Étudier la segmentation IoT et un VPN WireGuard si un accès distant devient
  nécessaire.

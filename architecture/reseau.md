# Architecture — réseau domestique

> Topologie du réseau local, adressage des machines et matrice des services.
> **Référence unique pour les IP** : toute doc ou config qui a besoin d'une
> adresse pointe ici — on ne duplique pas les IP au fil des documents.
> Dernière mise à jour : 10 juillet 2026
> Statut : IP constatées, **réservations DHCP pas encore faites** (backlog)

---

## 1. Vue d'ensemble

- **Box Bouygues** : routeur/DHCP du foyer, réseau local `192.168.1.0/24`.
- **Aucune exposition à Internet** : pas de redirection de port sur la box
  (principe n°1 de [securite.md](securite.md)).
- Routeur Asus RT-AX86U Pro **non branché** — réservé à un projet futur
  (VLAN, VPN, voir backlog).

```
Internet ═══ [ Box Bouygues ] ─── LAN 192.168.1.0/24 (Ethernet + WiFi)
                  │
   ┌──────────────┼──────────────────┬───────────────────────┐
   ▼              ▼                  ▼                       ▼
[ nas ]      [ jarvis-central ]   [ PC principal ]      [ téléphones,
 .80 (Eth)    .57 (Eth)            (DHCP dynamique)      satellites à venir… ]
```

---

## 2. Adressage des machines

| Machine | Hostname | IP | Connexion | Réservation DHCP |
|---|---|---|---|---|
| NAS (Pi 4) | `nas` / `nas.local` | **192.168.1.80** | Ethernet | ❌ à faire |
| Serveur Jarvis | `jarvis-central` | **192.168.1.57** | Ethernet | ❌ à faire |
| PC principal | — | dynamique | — | inutile (client) |
| Satellites (futurs) | — | — | WiFi | à réserver à l'ajout |

> ⚠️ Tant que les réservations DHCP ne sont pas faites sur la box, ces IP
> sont *stables en pratique* mais *non garanties* (un renouvellement de bail
> peut les changer). Les faire = priorité du backlog réseau.

## 3. Résolution de noms — convention

- **Machine → machine (configs, scripts, services)** : utiliser l'**IP**.
  Le mDNS (`.local`) dépend d'Avahi/systemd-resolved et peut échouer
  silencieusement entre serveurs headless — une config de service ne doit
  pas dépendre d'un mécanisme fragile.
- **Humain → machine (confort au quotidien)** : `nas.local` et les alias
  `~/.ssh/config` restent très bien depuis le PC.

## 4. Matrice des services (qui écoute où)

| Machine | Port | Service | Clients légitimes |
|---|---|---|---|
| nas | 22 | SSH (git + admin) | PC principal, jarvis-central |
| nas | 445 | SMB (partage Océane) | PC/téléphones de la famille |
| jarvis-central | 22 | SSH admin | PC principal |
| jarvis-central | 8123 | Home Assistant (web) | PC/téléphones de la famille |
| jarvis-central | 11434 | API Ollama | local uniquement (HA, futur agent) |
| jarvis-central | 10200 / 10300 / 10400 | Wyoming (piper / whisper / openwakeword) | local uniquement (HA, satellite) |
| jarvis-central | 10700 | wyoming-satellite « bureau » | local uniquement (HA) |

> Les ports « local uniquement » écoutent aujourd'hui sur tout le LAN — les
> restreindre à `127.0.0.1` est le must-have n°1 de
> [securite.md](securite.md) §3. Cette matrice est la base des futures
> règles UFW.

## 5. Évolutions prévues (backlog)

- Réservations DHCP (box Bouygues) pour nas et jarvis-central.
- Fiabiliser le lien RDC↔étage (Ethernet/CPL à terme).
- Routeur Asus : segmentation (VLAN IoT) et/ou VPN WireGuard si accès
  distant un jour.

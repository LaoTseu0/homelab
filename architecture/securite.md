# Sécurité du homelab — état et cible

> Posture de sécurité actuelle (honnête, sans complaisance), risques
> identifiés, et mesures proposées classées must-have / nice-to-have.
> Les actions retenues sont suivies dans [../backlog.md](../backlog.md).
> Dernière mise à jour : 18 juillet 2026
> Statut : **ébauche** — mesures proposées, arbitrage à venir

---

## 1. Principes (rappel de l'architecture)

1. **Rien d'exposé à Internet** : aucune redirection de port sur la box,
   accès local uniquement.
2. **Moindre privilège et cloisonnement** : comptes dédiés, conteneurs,
   chacun ne voit que ce dont il a besoin.
3. **Un agent autonome n'a jamais d'outil destructif** sans validation
   humaine (règle non négociable de la Phase 3).

---

## 2. État actuel — le tableau honnête

| Point | État | Commentaire |
|---|---|---|
| Exposition Internet | ✅ aucune | LAN only, pas de port forwardé sur la box |
| Cloisonnement NAS | ✅ bon | comptes `pinas` / groupe `agents` / `oce` séparés |
| SSH jarvis-central | ⚠️ | mot de passe encore accepté |
| Pare-feu jarvis-central | ❌ | aucun (UFW non configuré) |
| API Ollama (11434) | ⚠️ | ouverte à tout le LAN, **sans authentification** |
| Ports Wyoming (10200/10300/10400/10700) | ⚠️ | ouverts à tout le LAN, sans authentification |
| Conteneur HA | ⚠️ | `--privileged` = accès matériel très large |
| Mises à jour de sécurité | ⚠️ | manuelles (quand on y pense) |
| Backups | ❌ | aucun — ni config HA, ni données NAS |
| jarvis-core | 🕐 | machine raccordée au LAN, aucun service Jarvis installé — posture à définir en même temps que son API LLM (voir [inference.md](inference.md) §6) |

Lecture du risque : tout repose aujourd'hui sur la confiance dans le réseau
WiFi de la maison. Un appareil compromis sur le LAN (téléphone, IoT, PC
invité) pourrait parler à Ollama, aux services Wyoming, tenter du SSH.
Probabilité faible, mais coût de mitigation faible aussi.

---

## 3. Must-have (proposés — à arbitrer)

Par ordre de rapport protection/effort décroissant :

1. **Restreindre Ollama et Wyoming à `127.0.0.1`** — tous leurs clients
   (HA, satellite) sont sur la machine elle-même : publier ces ports
   (11434, 10200, 10300, 10400) sur l'interface locale seulement, dans le
   compose de [deploiement/jarvis-central/](../deploiement/jarvis-central/).
   Coût : 5 minutes. Le jour où un client distant existera (satellite sur
   Pi 5), on ouvrira ce port précis, pas tout.
2. **Pare-feu UFW sur jarvis-central** — politique deny entrant par défaut,
   n'autoriser que SSH (22) et HA (8123) depuis le sous-réseau local.
3. **SSH par clé uniquement** (`PasswordAuthentication no`) — supprime la
   surface « mot de passe devinable », aligne le serveur sur la philosophie
   déjà appliquée au NAS.
4. **`unattended-upgrades`** — les correctifs de sécurité Ubuntu s'installent
   seuls ; une machine 24/7 ne doit pas dépendre de « quand on y pense ».
5. **Backups** — config HA (`/srv/homeassistant`) et compose vers le NAS,
   puis SSD (même chantier que le backup NAS déjà au backlog). La sécurité,
   c'est aussi pouvoir reconstruire.
6. **Réévaluer le `--privileged` de HA** — il n'est pas indispensable
   aujourd'hui (pas de dongle branché) ; le remplacer par des accès ciblés
   (`--device /dev/ttyUSB0` quand le coordinateur Zigbee arrivera).

7. **API LLM de jarvis-core** (dès qu'elle existera) — pare-feu n'autorisant
   que `jarvis-central` sur le port d'inférence, SSH par clé uniquement,
   même posture que le reste du parc (voir [inference.md](inference.md) §6).

## 4. Nice-to-have (plus tard, si le besoin se précise)

- **Épingler les versions d'images Docker** (tags explicites plutôt que
  `latest`) — reproductibilité et pas de mise à jour surprise.
- **Comptes HA familiaux non-admin** — quand d'autres personnes utiliseront
  l'interface.
- **fail2ban** — surtout pertinent si un accès distant apparaît un jour.
- **Passphrase sur les clés SSH** de pc-admin.
- **Segmentation réseau / VLAN** (routeur Asus RT-AX86U Pro) — isoler l'IoT
  du reste ; projet réseau à part entière.
- **VPN** (WireGuard sur le routeur Asus) pour l'accès distant propre, si le
  besoin émerge — jamais d'exposition directe.

## 5. Non négociables pour la Phase 3 (couche agentique)

À relire **avant** d'installer Hermes/Pi :

- Conteneur dédié, sandboxé, **sans** accès au socket Docker, **sans** sudo.
- Aucun outil destructif (rm, reboot, écriture hors de son périmètre) sans
  validation humaine — pattern « pré-hook bloquant ».
- Accès NAS limité à ses dépôts (groupe `agents`) — jamais au partage d'Océane.
- Audit des CVE du framework choisi avant l'installation (leçon OpenClaw :
  ≈138 CVE début 2026).
- Rien d'exposé hors du LAN, comme tout le reste.

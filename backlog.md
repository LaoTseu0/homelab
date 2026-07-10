# Backlog

> Tout ce qui reste à faire, par thème. Les mesures de sécurité sont
> détaillées et justifiées dans [architecture/securite.md](architecture/securite.md).
> Dernière mise à jour : 10 juillet 2026

---

## Jarvis — finitions Phase 0

- [ ] **Accès git du serveur au NAS** : compte dédié dans le groupe `agents`
      sur le NAS + clé SSH de jarvis-central, puis `git clone
      nas:/srv/git/homelab.git ~/homelab` — fin du scp artisanal.
- [ ] **Exécuter `deploiement/jarvis-central/installer.sh`** sur le serveur :
      déploie le compose et le service systemd du satellite depuis le repo
      (fichiers prêts et versionnés — reste à exécuter).
- [ ] **Rattacher l'appareil « bureau » au pipeline Jarvis-HA** et vérifier que
      les instructions (français, réponses brèves) s'appliquent bien en vocal
      (réponse « hydrogène » trop longue lors du test).
- [ ] **Trancher le `--mic-volume-multiplier`** — tests à différentes distances,
      avec `--debug-recording-dir` pour écouter ce que Whisper reçoit ; reporter
      la décision dans `wyoming-satellite.service` (repo).
- [ ] **Retirer les flags de debug** (`--debug-probability` sur openwakeword)
      de la config une fois les réglages stabilisés — NB : le compose du repo
      ne les a jamais eus, celui du serveur a divergé → l'installer.sh remettra
      le serveur en conformité.

## Sécurité — must-have (voir architecture/securite.md §3)

- [ ] **Pare-feu UFW sur jarvis-central** (deny entrant par défaut, ouvertures
      explicites limitées au LAN).
- [ ] **Restreindre Ollama (11434) et les ports Wyoming à 127.0.0.1** — aucun
      client distant aujourd'hui, aucune raison d'écouter sur tout le LAN.
- [ ] **SSH par clé uniquement** sur jarvis-central (`PasswordAuthentication no`),
      aligné sur la philosophie du NAS.
- [ ] **unattended-upgrades** — correctifs de sécurité automatiques.
- [ ] **Backup de `/srv/homeassistant` + compose** vers NAS puis SSD (rsync).
- [ ] **Réévaluer le `--privileged` du conteneur HA** — le remplacer par des
      accès ciblés (`--device`) quand le dongle Zigbee arrivera.

## Jarvis — Phase 1 et suite

- [ ] Enceinte + boîtier définitifs pour le satellite salon (XVF3800, loin de la TV).
- [ ] **Wake word custom « ok jarvis »** — entraînement openWakeWord avec
      prononciation française (notebook Colab, ~1 h).
- [ ] Satellites pièces secondaires (ESP32-S3 / S3-BOX-3).
- [ ] Dépôt `jarvis-memory` (convention OKF) + Obsidian + git NAS — Phase 2.
- [ ] Couche agentique (Hermes/Pi) sandboxée — Phase 3 (voir les non-négociables
      de sécurité, architecture/securite.md §5).

## NAS

- [ ] Acheter un **adaptateur USB-SATA** pour le SSD Kingston.
- [ ] **Backup automatique** (rsync + cron) des dépôts git + dossier Océane vers le SSD.
- [ ] (Plus tard) Migrer le stockage primaire microSD → disque durable.
- [ ] (Optionnel) Clés SSH dédiées par agent + comptes par agent.
- [ ] (Optionnel) Accès distant via VPN (routeur Asus RT-AX86U Pro).
- [ ] (Optionnel) Passphrase sur la clé SSH du PC principal.
- [ ] (Optionnel) Découper plus finement la doc NAS si elle grossit.

## Réseau (voir architecture/reseau.md)

- [ ] **Réservations DHCP** (box Free) pour `nas` (192.168.1.80) et
      `jarvis-central` (192.168.1.57) — les IP sont documentées mais non
      garanties tant que ce n'est pas fait.
- [ ] Lien RDC↔étage : surveiller la fiabilité WiFi, Ethernet/CPL à terme.

# Backlog

> Tout ce qui reste à faire, par thème. Les mesures de sécurité sont
> détaillées et justifiées dans [architecture/securite.md](architecture/securite.md).
> Dernière mise à jour : 23 juillet 2026

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
- [ ] **Session de conception : routeur multi-modèles** — dérouler les
      questions ouvertes de architecture/router-multi-model.md (long terme,
      dépend d'un GPU plus gros).

## jarvis-core — tour d'inférence (voir architecture/inference.md)

- [ ] **Trancher le modèle résident** (candidats en inference.md §4) et le
      **serveur d'inférence** (llama.cpp / Ollama / vLLM).
- [ ] **Trancher le port/API exposés** à jarvis-central + restriction pare-feu
      (architecture/securite.md §3.7).
- [ ] **Trancher la politique d'alimentation** (24/7, manuelle, ou WoL depuis
      jarvis-central).
- [ ] **Vérifier le profil EXPO de la RAM** (DDR5-6000 attendu — désactivé,
      ~25 % de débit d'offload perdus).
- [ ] **Vérifier alimentation + slots PCIe** — conditionne l'option future
      « second GPU 24 Go ».
- [ ] **Documenter le socle** : créer `serveurs/jarvis-core/installation.md`
      au montage, tenir `etat.md` à jour.

## NAS

- [ ] Acheter un **adaptateur USB-SATA** pour le SSD Kingston.
- [ ] **Backup automatique** (rsync + cron) des dépôts git + dossier Océane vers le SSD.
- [ ] (Plus tard) Migrer le stockage primaire microSD → disque durable.
- [ ] **Miroir GitHub pour les comptes `agents`** : le hook `post-receive`
      s'exécute sous le compte qui pousse, et seul `pinas` a la clé GitHub —
      les pushes des agents ne seront donc pas miroités. Piste : le hook dépose
      un marqueur, une unité systemd en `pinas` fait le push
      (serveurs/nas/installation.md §4.4).
- [ ] **Étendre le miroir à `memoire-agent.git`** si le besoin se confirme —
      vérifier d'abord qu'aucun secret n'y est versionné (dépôt privé exigé).
- [ ] (Optionnel) Clés SSH dédiées par agent + comptes par agent.
- [ ] (Optionnel) Accès distant via VPN (routeur Asus RT-AX86U Pro).
- [ ] (Optionnel) Passphrase sur les clés SSH de pc-admin.
- [ ] (Optionnel) Découper plus finement la doc NAS si elle grossit.

## Supervision des machines

> Déclencheur : génération LLM débridée le 19 juillet 2026 (sampling
> temperature 1.5 sans limite de tokens → GPU à fond et ventilateurs
> plein régime sur jarvis-central jusqu'au timeout client). Sans
> supervision, on ne voit l'emballement que quand on entend les ventilos.

- [ ] **Choisir la brique de monitoring** : léger et immédiat (Netdata ou
      Beszel, un conteneur par machine, dashboards + alertes sans config)
      **vs** stack complète Prometheus + node_exporter + Grafana +
      Alertmanager (plus de travail, mais compétence marché et alignée
      couche T de [formation/roadmap.md](formation/roadmap.md)).
      Piste : commencer léger, la stack pro comme projet d'apprentissage.
- [ ] **Métriques GPU de jarvis-central** (température, VRAM, charge —
      exporter nvidia-smi ou équivalent selon la brique choisie) ;
      à étendre à jarvis-core (RTX 4090) dès son socle installé.
- [ ] **Alertes** température/charge prolongée → notification (pas de
      coupure automatique : les GPU se protègent seuls par throttling ;
      couper une machine est une décision humaine).
- [ ] **Borner les charges plutôt que tuer les machines** : `num_predict`
      systématique dans les appels LLM (fait dans le notebook 04), timeouts
      client, et à terme quotas côté serveur d'inférence.
- [ ] (Optionnel) **Uptime des services** (Uptime Kuma) : Ollama, HA,
      satellite Wyoming, NAS.

## Réseau (voir architecture/reseau.md)

- [ ] **Réservations DHCP** (box Bouygues) pour `nas` (192.168.1.80),
      `jarvis-central` (192.168.1.57), `jarvis-core` (192.168.1.187) et
      `pc-admin` — les IP sont documentées mais non garanties tant que ce
      n'est pas fait.
- [ ] Lien RDC↔étage : surveiller la fiabilité WiFi, Ethernet/CPL à terme.

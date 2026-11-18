# Backlog

> Tout ce qui reste à faire, par thème. Les mesures de sécurité sont
> détaillées et justifiées dans [architecture/securite.md](architecture/securite.md).
> Dernière mise à jour : 23 août 2026

---

## Jarvis — finitions Phase 0

- [ ] **Accès git du serveur au NAS** : compte dédié dans le groupe `agents`
      sur le NAS + clé SSH de lab-studio, puis `git clone
      nas:/srv/git/homelab.git ~/homelab` — fin du scp artisanal.
- [ ] **Exécuter `deploiement/lab-studio/installer.sh`** sur le serveur :
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

- [ ] **Pare-feu UFW sur lab-studio** (deny entrant par défaut, ouvertures
      explicites limitées au LAN).
- [ ] **Restreindre Ollama (11434) et les ports Wyoming à 127.0.0.1** — aucun
      client distant aujourd'hui, aucune raison d'écouter sur tout le LAN.
- [ ] **SSH par clé uniquement** sur lab-studio (`PasswordAuthentication no`),
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
- [ ] **Trancher le port/API exposés** à lab-studio + restriction pare-feu
      (architecture/securite.md §3.7).
- [ ] **Trancher la politique d'alimentation** (24/7, manuelle, ou WoL depuis
      lab-studio).
- [ ] **Vérifier le profil EXPO de la RAM** (DDR5-6000 attendu — désactivé,
      ~25 % de débit d'offload perdus).
- [ ] **Vérifier alimentation + slots PCIe** — conditionne l'option future
      « second GPU 24 Go ».
- [ ] **Documenter le socle** : créer `serveurs/jarvis-core/installation.md`
      au montage, tenir `etat.md` à jour.

## NAS

### Reconstruction Pi 5 et administration commune — 6 novembre 2026

- [x] Choisir Linux + Ansible + Compose comme modèle commun.
- [x] Préparer inventaire, audit, rôles base/Docker/NAS et reprise des Compose Jarvis dans `infra/`.
- [x] Vérifier la lecture gzip et l'inventaire de l'archive Pi 4 sur le PC.
- [ ] Confirmer IP, accès SSH, version d'OS et disques du Pi 5.
- [ ] Installer le contrôleur Linux avec mise, puis valider et exécuter Ansible.
- [ ] Restaurer les quatre dépôts et partages, vérifier les propriétaires et tester les accès.
- [ ] Comparer GitHub avant de réactiver les trois hooks de miroir.
- [ ] Valider le stockage NVMe et les sauvegardes sur support distinct.
- [ ] Déployer le registry privé et publier une image versionnée de l'exporteur.
- [ ] Valider la reprise de lab-studio puis retirer son installateur historique.

### Suivi historique Pi 4 (à réconcilier après restauration)

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

## Observabilité et supervision de Jarvis

> Déclencheur : génération LLM débridée le 19 juillet 2026 (sampling
> temperature 1.5 sans limite de tokens → GPU à fond et ventilateurs
> plein régime sur lab-studio jusqu'au timeout client). Sans
> supervision, on ne voit l'emballement que quand on entend les ventilos.

> Décision : socle initial volontairement réduit à **Prometheus + Grafana +
> node_exporter + un `jarvis-exporter` modulaire**. Pas de proxy dans le
> chemin critique, pas de modification des images officielles et pas de
> Tempo/Loki/cAdvisor/DCGM/Alertmanager/Uptime Kuma sans besoin mesuré.
> Toute la configuration est versionnée sous `deploiement/lab-studio/`
> et déployée par son `installer.sh`. Le cœur vocal et l'observabilité vivent
> dans deux fichiers Compose séparés que l'installateur combine.

- [x] **Préparer le socle d'observabilité en config-as-code** : Compose
      séparé, Prometheus, Grafana provisionné, node_exporter et
      `jarvis-exporter` à connecteurs indépendants (Home Assistant, Ollama,
      NVIDIA). Les benchmarks Ollama sont exclusivement manuels : aucune
      sonde périodique ne doit réveiller le GPU.
- [ ] **Déployer et valider le socle sur `lab-studio`** avec
      `deploiement/lab-studio/installer.sh`, puis vérifier la persistance
      des données après recréation des conteneurs.
- [ ] **Épingler les versions des cinq images du cœur vocal** après validation
      de leurs versions actuelles. L'observabilité est épinglée, mais les tags
      flottants du Compose principal empêchent encore une reconstruction
      strictement identique à une date ultérieure.
- [ ] **Configurer le jeton Home Assistant** hors Git pour la collecte passive
      des événements Assist, puis valider les durées pipeline, STT, intent/LLM
      et TTS. Ne stocker ni prompt, ni transcription, ni réponse.
- [ ] **Valider les métriques machine et GPU de `lab-studio`** : CPU, RAM,
      disque, réseau, température, VRAM, charge et puissance GPU ; étendre à
      `jarvis-core` (RTX 4090) dès que son socle est installé.
- [ ] **Configurer le canal de notification des alertes** température,
      indisponibilité et latence prolongées. Pas de coupure automatique : les
      GPU se protègent par throttling et arrêter une machine reste une décision
      humaine.
- [ ] **Mesurer la latence réellement perçue** : compléter les événements
      Home Assistant (`tts-end`) par `playback_started` côté satellite afin de
      suivre « fin de parole → début du son ».
- [ ] **Borner les charges plutôt que tuer les machines** : `num_predict`
      systématique dans les appels LLM (fait dans le notebook 04), timeouts
      client, et à terme quotas côté serveur d'inférence.

## Réseau (voir architecture/reseau.md)

- [ ] **Réservations DHCP** (box Bouygues) pour `nas` (192.168.1.80),
      `lab-studio` (192.168.50.252), `jarvis-core` (192.168.1.187) et
      `pc-admin` — les IP sont documentées mais non garanties tant que ce
      n'est pas fait.
- [ ] Lien RDC↔étage : surveiller la fiabilité WiFi, Ethernet/CPL à terme.

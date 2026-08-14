# Homelab — runbook d'installation

> Rôle : regrouper, dans l'ordre, les commandes nécessaires pour reconstruire
> le homelab documenté.
> Date de consolidation : 31 juillet 2026.
> Référence d'architecture :
> [`reference-homelab.md`](reference-homelab.md).
> Ce runbook n'utilise pas le backlog et ne remplace pas les fichiers de
> déploiement versionnés.

## 0. Règles d'utilisation

- Lire entièrement une section avant d'en exécuter les commandes.
- Exécuter chaque bloc sur la machine indiquée au-dessus du bloc.
- Ne jamais exécuter les commandes `docker run` historiques après le
  déploiement Compose : elles créeraient des conteneurs et ports en conflit.
- Les adresses actuellement documentées sont :
  - NAS : `192.168.1.80` ;
  - `jarvis-central` : `192.168.1.57` ;
  - `jarvis-core` : `192.168.1.187`.
- Ces IP ne sont pas garanties tant que les réservations DHCP ne sont pas
  configurées sur la box.
- Les secrets, mots de passe et clés privées ne doivent jamais être ajoutés à
  ce dépôt.

## 1. `jarvis-central` — de l'OS au test GPU dans un conteneur

Cette section produit le socle suivant : Ubuntu Server, SSH, pilote NVIDIA,
Docker, NVIDIA Container Toolkit, puis un `nvidia-smi` réussi depuis Docker.

### 1.1 Installer Ubuntu Server

Actions manuelles, avec écran et clavier temporairement branchés :

1. Créer une clé USB Ubuntu Server 26.04 LTS avec Rufus.
2. Installer Ubuntu Server, pas la variante `minimized`.
3. Définir le hostname `jarvis-central`.
4. Créer l'utilisateur `jarvis`.
5. Cocher `Install OpenSSH server`.
6. Redémarrer puis vérifier l'accès SSH avant de retirer écran et clavier.
7. Dans le BIOS, régler si possible le redémarrage après coupure secteur sur
   `Power On`.

Toutes les commandes suivantes sont exécutées sur `jarvis-central` avec le
compte `jarvis`.

### 1.2 Mettre le système à jour

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y ca-certificates curl git gnupg alsa-utils python3-venv
```

### 1.3 Installer et valider le pilote NVIDIA

```bash
sudo ubuntu-drivers install
sudo reboot
```

Après reconnexion SSH :

```bash
nvidia-smi
```

Résultat attendu : la GeForce RTX 2060 et ses 6144 MiB de VRAM apparaissent.

### 1.4 Installer Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker jarvis
```

Fermer complètement la session afin de charger le nouveau groupe :

```bash
exit
```

Après reconnexion :

```bash
docker version
docker compose version
docker run --rm hello-world
```

### 1.5 Installer NVIDIA Container Toolkit

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### 1.6 Test final : `nvidia-smi` dans un conteneur

```bash
docker info | grep -i nvidia
docker run --rm --gpus all ubuntu nvidia-smi
```

Le second `nvidia-smi` doit afficher la même RTX 2060 que sur l'hôte. Cette
validation termine l'installation du socle GPU.

## 2. NAS — Raspberry Pi OS, Git et Samba

### 2.1 Installer Raspberry Pi OS

Dans Raspberry Pi Imager :

1. sélectionner Raspberry Pi OS Lite 64 bits ;
2. définir le hostname `nas` ;
3. créer l'utilisateur `pinas` ;
4. activer SSH ;
5. démarrer le Pi en Ethernet.

Toutes les commandes de cette section sont ensuite exécutées sur le NAS avec
le compte `pinas`.

### 2.2 Mettre le système à jour et installer les services

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y git samba
sudo systemctl enable --now ssh
sudo systemctl enable --now smbd
```

Vérifier l'identité et l'adresse obtenue :

```bash
hostname
hostname -I
systemctl status ssh --no-pager
systemctl status smbd --no-pager
```

### 2.3 Créer le groupe Git et `/srv/git`

```bash
sudo groupadd --force agents
sudo mkdir -p /srv/git
sudo chown pinas:agents /srv/git
sudo chmod 2775 /srv/git
git config --global init.defaultBranch main
```

Vérifier les droits effectifs :

```bash
ls -ld /srv/git
getent group agents
```

Attention : avec le mode `2775`, les membres du groupe `agents` peuvent
techniquement créer, renommer et supprimer des entrées dans `/srv/git`. Voir
la section sur cet écart dans
[`reference-homelab.md`](reference-homelab.md#44-écart-de-permissions-important).

### 2.4 Créer les dépôts bare existants

Ne lancer chaque création que si le dépôt correspondant n'existe pas déjà :

```bash
sudo -u pinas git init --bare --shared=group /srv/git/homelab.git
sudo -u pinas git init --bare --shared=group /srv/git/memoire-agent.git

sudo git config --system --add safe.directory /srv/git/homelab.git
sudo git config --system --add safe.directory /srv/git/memoire-agent.git
```

Configurer explicitement `main` comme branche par défaut des dépôts :

```bash
sudo -u pinas git -C /srv/git/homelab.git symbolic-ref HEAD refs/heads/main
sudo -u pinas git -C /srv/git/memoire-agent.git symbolic-ref HEAD refs/heads/main
```

Vérifications :

```bash
sudo -u pinas git -C /srv/git/homelab.git config --get core.sharedRepository
sudo -u pinas git -C /srv/git/homelab.git symbolic-ref HEAD
sudo git config --system --get-all safe.directory
```

### 2.5 Créer le compte Git dédié à `jarvis-central`

Le compte `jarvisc` est mentionné dans l'état existant de `jarvis-central`,
mais sa création n'était pas documentée. Les commandes suivantes définissent
le modèle minimal cohérent : compte sans sudo, membre du groupe `agents`, accès
Git par SSH.

```bash
sudo adduser --disabled-password --gecos "" jarvisc
sudo usermod -aG agents jarvisc
id jarvisc
```

La clé publique de `jarvis-central` sera installée en section 4.2. Tant que
cette étape n'est pas faite, ce compte ne peut pas se connecter.

### 2.6 Créer le compte et le partage Samba d'Océane

Créer un compte Linux sans mot de passe utilisable et sans shell :

```bash
sudo adduser --disabled-password --gecos "" --shell /usr/sbin/nologin oce
sudo mkdir -p /srv/partages/oceane
sudo chown oce:oce /srv/partages/oceane
sudo chmod 0700 /srv/partages/oceane
sudo smbpasswd -a oce
```

Ouvrir la configuration Samba :

```bash
sudoedit /etc/samba/smb.conf
```

Ajouter à la fin du fichier :

```ini
[Oceane]
   path = /srv/partages/oceane
   valid users = oce
   read only = no
   browseable = yes
   create mask = 0600
   directory mask = 0700
```

Valider puis recharger Samba :

```bash
sudo testparm
sudo systemctl restart smbd
systemctl status smbd --no-pager
```

Accès depuis Windows : `\\192.168.1.80\Oceane`, utilisateur `oce`.

## 3. `pc-admin` — clés et alias SSH

Toutes les commandes de cette section sont exécutées dans PowerShell sur le PC
Windows d'administration.

### 3.1 Créer le dossier SSH

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.ssh"
```

### 3.2 Créer une clé distincte par machine

Ne pas relancer une commande si le fichier privé correspondant existe déjà.

```powershell
ssh-keygen -t ed25519 -C "pc-admin" -f "$env:USERPROFILE\.ssh\id_ed25519_nas"
ssh-keygen -t ed25519 -C "pc-admin" -f "$env:USERPROFILE\.ssh\id_ed25519_jarvis-central"
```

La clé de `jarvis-core` sera créée lorsque son compte administrateur aura été
décidé :

```powershell
ssh-keygen -t ed25519 -C "pc-admin" -f "$env:USERPROFILE\.ssh\id_ed25519_jarvis-core"
```

### 3.3 Déposer les clés publiques

```powershell
Get-Content "$env:USERPROFILE\.ssh\id_ed25519_nas.pub" | ssh pinas@192.168.1.80 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

Get-Content "$env:USERPROFILE\.ssh\id_ed25519_jarvis-central.pub" | ssh jarvis@192.168.1.57 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

### 3.4 Déclarer les alias

Ouvrir le fichier de configuration :

```powershell
notepad "$env:USERPROFILE\.ssh\config"
```

Y placer :

```sshconfig
Host nas
    HostName 192.168.1.80
    User pinas
    IdentityFile C:\Users\antho\.ssh\id_ed25519_nas
    IdentitiesOnly yes

Host jarvis-central
    HostName 192.168.1.57
    User jarvis
    IdentityFile C:\Users\antho\.ssh\id_ed25519_jarvis-central
    IdentitiesOnly yes

Host jarvis-core
    HostName 192.168.1.187
    User A_COMPLETER
    IdentityFile C:\Users\antho\.ssh\id_ed25519_jarvis-core
    IdentitiesOnly yes
```

### 3.5 Tester les accès

```powershell
ssh nas
ssh jarvis-central
```

`ssh jarvis-core` ne peut être validé qu'après installation de son OS et
création de son compte administrateur.

### 3.6 Alimenter un dépôt NAS fraîchement créé

Cette étape est nécessaire uniquement si `/srv/git/homelab.git` vient d'être
créé et ne contient encore aucune branche. Depuis PowerShell, dans la copie de
travail actuelle :

```powershell
Set-Location C:\Dev\Projets\homelab

if ((git remote) -notcontains "nas") {
    git remote add nas nas:/srv/git/homelab.git
}

git push nas main
git push nas --tags
```

Vérifier ensuite sur le NAS :

```bash
git -C /srv/git/homelab.git log --oneline -5
git -C /srv/git/homelab.git symbolic-ref HEAD
```

## 4. `jarvis-central` — accès Git au NAS

### 4.1 Générer une clé dédiée au NAS

Sur `jarvis-central`, avec le compte `jarvis` :

```bash
ssh-keygen -t ed25519 -C "jarvis-central -> nas" -f ~/.ssh/id_ed25519_nas
cat ~/.ssh/id_ed25519_nas.pub
```

### 4.2 Autoriser la clé pour `jarvisc`

Copier la ligne affichée par la commande précédente. Sur le NAS, connecté en
`pinas` :

```bash
sudo install -d -o jarvisc -g jarvisc -m 0700 /home/jarvisc/.ssh
sudoedit /home/jarvisc/.ssh/authorized_keys
sudo chown jarvisc:jarvisc /home/jarvisc/.ssh/authorized_keys
sudo chmod 0600 /home/jarvisc/.ssh/authorized_keys
```

Coller uniquement la clé publique dans `authorized_keys`, jamais la clé privée.

### 4.3 Créer l'alias NAS sur `jarvis-central`

Sur `jarvis-central` :

```bash
nano ~/.ssh/config
```

Ajouter :

```sshconfig
Host nas
    HostName 192.168.1.80
    User jarvisc
    IdentityFile /home/jarvis/.ssh/id_ed25519_nas
    IdentitiesOnly yes
```

Puis appliquer les permissions et tester :

```bash
chmod 0600 ~/.ssh/config
ssh nas
```

Le premier accès demande de confirmer l'empreinte du NAS. La vérifier avant de
répondre `yes`.

## 5. `jarvis-central` — déployer Jarvis

La source de vérité est le dossier
[`deploiement/jarvis-central/`](deploiement/jarvis-central/). L'installeur crée
les répertoires persistants, copie le Compose, lance les cinq conteneurs,
télécharge les modèles et installe l'unité systemd du satellite.

### 5.1 Cloner le dépôt depuis le NAS

Sur `jarvis-central` :

```bash
git clone nas:/srv/git/homelab.git ~/homelab
cd ~/homelab
git status
```

### 5.2 Vérifier le matériel audio

Brancher le ReSpeaker XVF3800 en USB et l'enceinte sur sa sortie audio, puis :

```bash
lsusb
arecord -l
aplay -l
```

La carte doit apparaître avec le nom ALSA `Array`.

### 5.3 Exécuter l'installeur versionné

```bash
cd ~/homelab/deploiement/jarvis-central
chmod +x installer.sh
./installer.sh
```

L'installeur exécute notamment les opérations suivantes :

```bash
sudo mkdir -p /srv/jarvis /srv/homeassistant /srv/wyoming/whisper /srv/wyoming/piper
docker volume inspect ollama >/dev/null 2>&1 || docker volume create ollama
sudo cp /home/jarvis/homelab/deploiement/jarvis-central/docker-compose.yml /srv/jarvis/docker-compose.yml
docker compose -f /srv/jarvis/docker-compose.yml up -d
docker exec ollama ollama pull qwen3:4b-instruct-2507-q4_K_M
docker exec ollama ollama pull nomic-embed-text
git clone https://github.com/rhasspy/wyoming-satellite.git /home/jarvis/wyoming-satellite
(cd /home/jarvis/wyoming-satellite && script/setup)
sudo cp /home/jarvis/homelab/deploiement/jarvis-central/wyoming-satellite.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now wyoming-satellite
```

Ce bloc est fourni pour comprendre l'installation. Quand `installer.sh` a été
exécuté, ne pas le rejouer commande par commande.

### 5.4 Vérifier les conteneurs et le service hôte

```bash
docker ps
docker compose -f /srv/jarvis/docker-compose.yml ps
systemctl status wyoming-satellite --no-pager
```

Les cinq conteneurs attendus sont :

- `ollama` ;
- `homeassistant` ;
- `whisper` ;
- `piper` ;
- `openwakeword`.

### 5.5 Tester Ollama

Test interactif :

```bash
docker exec -it ollama ollama run qwen3:4b-instruct-2507-q4_K_M
```

Quitter avec `/bye`.

Test HTTP :

```bash
curl http://127.0.0.1:11434/api/generate -d '{
  "model": "qwen3:4b-instruct-2507-q4_K_M",
  "prompt": "Dis bonjour en une phrase.",
  "stream": false
}'
```

### 5.6 Contrôler les ports

```bash
sudo ss -lntp | grep -E ':(22|8123|10200|10300|10400|10700|11434)\b'
```

Dans la configuration actuelle, Ollama et Wyoming sont publiés sur le LAN. Ce
runbook reproduit l'existant ; il ne prétend pas que ces ports sont restreints
à la boucle locale.

## 6. Home Assistant — configuration après installation

Cette partie se fait dans l'interface web, pas en ligne de commande.

Ouvrir : `http://192.168.1.57:8123`.

### 6.1 Onboarding

1. Créer le compte administrateur Home Assistant.
2. Régler la localisation et le fuseau sur `Europe/Paris`.

### 6.2 Intégration Ollama

Ajouter l'intégration Ollama avec :

- URL : `http://127.0.0.1:11434` ;
- modèle : `qwen3:4b-instruct-2507-q4_K_M` ;
- contrôle Home Assistant par appels d'outils activé.

Créer l'assistant vocal `Jarvis`, langue française, puis ajouter une consigne
de réponse courte et systématiquement en français.

### 6.3 Intégrations Wyoming

Ajouter une intégration Wyoming Protocol par service :

| Service | Hôte | Port |
|---|---|---:|
| Piper | `127.0.0.1` | `10200` |
| Whisper | `127.0.0.1` | `10300` |
| openWakeWord | `127.0.0.1` | `10400` |
| Satellite `bureau` | `127.0.0.1` | `10700` |

Dans l'assistant `Jarvis` :

- voix vers texte : faster-whisper ;
- texte vers voix : Piper, voix `fr_FR-siwis-medium` ;
- traitement local complet ;
- wake word : `hey_jarvis`.

## 7. NAS — miroir GitHub optionnel

Cette section configure le miroir sortant `NAS → GitHub`. Son activation
réelle n'est pas confirmée dans l'état actuel. Ne l'exécuter qu'après création
d'un dépôt GitHub privé et vide.

Toutes les commandes sont exécutées sur le NAS avec `pinas`.

### 7.1 Créer la clé du miroir

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_github -N "" -C "nas -> github"
cat ~/.ssh/id_ed25519_github.pub
```

Dans GitHub, ajouter la clé publique comme Deploy Key du dépôt `homelab`, avec
`Allow write access`. Ne jamais publier la clé privée.

### 7.2 Configurer l'hôte GitHub

```bash
nano ~/.ssh/config
```

Ajouter :

```sshconfig
Host github.com
    HostName github.com
    User git
    IdentityFile /home/pinas/.ssh/id_ed25519_github
    IdentitiesOnly yes
```

Puis :

```bash
chmod 0600 ~/.ssh/config
ssh-keyscan github.com >> ~/.ssh/known_hosts
ssh -T git@github.com
```

### 7.3 Ajouter le remote

Remplacer `COMPTE_GITHUB` par le nom du compte réel :

```bash
GITHUB_ACCOUNT="COMPTE_GITHUB"
sudo -u pinas git -C /srv/git/homelab.git remote add github "git@github.com:${GITHUB_ACCOUNT}/homelab.git"
sudo -u pinas git -C /srv/git/homelab.git remote -v
```

Ne pas exécuter `remote add` une seconde fois si le remote existe déjà. Dans ce
cas, vérifier ou corriger son URL avec :

```bash
GITHUB_ACCOUNT="COMPTE_GITHUB"
sudo -u pinas git -C /srv/git/homelab.git remote set-url github "git@github.com:${GITHUB_ACCOUNT}/homelab.git"
```

### 7.4 Installer le hook `post-receive`

Le hook est versionné dans le dépôt — on ne l'écrit pas à la main. Depuis un
clone du repo sur le NAS, en tant que `pinas` :

```bash
cd ~/homelab/deploiement/nas
./installer-miroir.sh
```

Le script installe le hook sur **tous** les dépôts de `/srv/git/` ayant un
remote `github`, sauvegarde l'ancienne version en `post-receive.bak` et pose
les permissions. Il est idempotent.

Détail du hook et de ce qu'il diagnostique :
[serveurs/nas/installation.md](serveurs/nas/installation.md) §4.3.

### 7.5 Tester le miroir

Depuis un clone de travail :

```bash
git push origin main
```

Puis sur le NAS :

```bash
sudo -u pinas git -C /srv/git/homelab.git ls-remote github main
```

Rattrapage manuel si le miroir a pris du **retard** (GitHub avait été
injoignable) :

```bash
sudo -u pinas git -C /srv/git/homelab.git push github --all
sudo -u pinas git -C /srv/git/homelab.git push github --tags
```

> Si le hook affiche `DIVERGENCE`, ce rattrapage **ne s'applique pas** et
> échouera de la même façon : GitHub porte un commit absent du NAS, il faut
> arbitrer. Procédure complète dans
> [serveurs/nas/installation.md](serveurs/nas/installation.md) §4.5.

Le hook s'exécute avec l'identité Unix qui pousse. Comme la clé GitHub est
privée à `pinas`, les pushes effectués sous `jarvisc` ou un autre compte agent
mettront à jour le NAS mais ne pourront pas alimenter ce miroir directement.

## 8. Exploitation courante de `jarvis-central`

### 8.1 Mettre à jour la configuration versionnée

```bash
cd ~/homelab
git pull
cd deploiement/jarvis-central
./installer.sh
```

### 8.2 Gérer les conteneurs

```bash
docker compose -f /srv/jarvis/docker-compose.yml up -d
docker compose -f /srv/jarvis/docker-compose.yml pull
docker compose -f /srv/jarvis/docker-compose.yml up -d
docker compose -f /srv/jarvis/docker-compose.yml down
```

`down` arrête et supprime les conteneurs Compose, mais conserve les bind mounts
et le volume externe `ollama`.

### 8.3 Consulter les journaux

```bash
docker compose -f /srv/jarvis/docker-compose.yml logs -f
journalctl -u wyoming-satellite -f
```

### 8.4 Redémarrer le satellite vocal

```bash
sudo systemctl restart wyoming-satellite
systemctl status wyoming-satellite --no-pager
```

## 9. `jarvis-core` — installation non définie

Ne pas inventer de commandes d'installation pour `jarvis-core`. L'état actuel
ne définit encore ni :

- l'OS ;
- le compte administrateur ;
- le serveur d'inférence ;
- le modèle résident ;
- le port ou le format de l'API ;
- la politique d'alimentation.

L'adresse constatée est `192.168.1.187`, mais elle ne suffit pas à produire un
runbook reproductible.

## 10. Sources détaillées conservées

- [`serveurs/jarvis-central/installation.md`](serveurs/jarvis-central/installation.md)
- [`serveurs/jarvis-central/etat.md`](serveurs/jarvis-central/etat.md)
- [`deploiement/jarvis-central/`](deploiement/jarvis-central/)
- [`serveurs/nas/installation.md`](serveurs/nas/installation.md)
- [`serveurs/pc-admin/installation.md`](serveurs/pc-admin/installation.md)
- [`reference-homelab.md`](reference-homelab.md)

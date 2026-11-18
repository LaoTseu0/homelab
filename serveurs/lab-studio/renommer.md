# Renommer la tour en lab-studio

La tour passe de `jarvis-central` à `lab-studio`. Son compte d’administration
`jarvis` devient `studio`, avec le même UID et le dossier `/home/studio`.
L’inventaire Ansible et l’alias SSH Windows utilisent déjà les nouveaux noms.
Le dernier bail connu est `192.168.50.252`. Le projet Compose `jarvis` continue
d’utiliser ses volumes existants et sa configuration sous `/srv/jarvis`.

## 1. Préparer un accès de secours

**Sur le clavier et l’écran de la tour**, depuis le compte `jarvis` :

```bash
id jarvis
getent passwd jarvis studio
getent group jarvis studio
ls -ld /home/jarvis
ls -ld /home/studio
ip -br -4 addr show enp4s0
sudo systemctl status wyoming-satellite --no-pager
```

Note l’UID, le GID et les groupes de `jarvis`. Vérifie que le compte et le
groupe `studio` ainsi que le chemin `/home/studio` sont libres. Si le home
actuel est monté séparément, relève son montage avant de poursuivre. Si le
bail DHCP a changé, corrige l’IP dans l’inventaire et l’alias SSH Windows.
Sauvegarde les fichiers importants du home et vérifie que la copie est lisible.

Crée un accès administrateur temporaire. Le mot de passe demandé par
`adduser` est celui de ce compte de secours.

```bash
sudo adduser migration-studio
sudo adduser migration-studio sudo
```

Ouvre une deuxième console locale, par exemple avec `Ctrl+Alt+F3`, et
connecte-toi en `migration-studio`. Vérifie `sudo -v`, puis ouvre un shell
d’administration avec `sudo -i`. Garde cette console accessible jusqu’à la
fin des tests SSH et sudo.

## 2. Renommer le compte et la machine

**Dans le shell root de la deuxième console**, sauvegarde la configuration
et note l’état initial.

```bash
umask 077
backup=$(mktemp -d /root/bascule-lab-studio.XXXXXX)
printf '%s\n' "$backup"
cp -a /etc/hostname /etc/hosts "$backup/"
id jarvis > "$backup/id.jarvis"
crontab -u jarvis -l > "$backup/crontab.jarvis"
```

Si `crontab` indique qu’aucune table n’existe, le fichier est vide. En cas
d’autre erreur, vérifie-la avant de poursuivre. Repère les références au compte
dans les fichiers locaux. Les instructions du satellite sont traitées plus bas.

```bash
grep -nE '(^|[^[:alnum:]_-])jarvis([^[:alnum:]_-]|$)' \
  /etc/hosts /etc/fstab /etc/sudoers /etc/sudoers.d/* \
  /etc/ssh/sshd_config /etc/ssh/sshd_config.d/* \
  /etc/systemd/system/*.service /etc/cron.d/* /home/jarvis/.ssh/config \
  2>/dev/null
```

Arrête le satellite s’il est installé, puis ferme les sessions de `jarvis`.
La commande `loginctl` déconnecte les sessions restantes de ce compte et
peut couper leur accès SSH. Termine les services qui utilisent encore son UID
selon leur méthode d’arrêt habituelle.

```bash
systemctl stop wyoming-satellite.service  # Seulement si l’unité existe.
loginctl terminate-user jarvis           # Seulement s’il reste des sessions.
pgrep -a -u jarvis
```

Quand `pgrep` ne montre plus aucun processus, renomme le compte. Le
changement de nom et le déplacement du home se font dans la même commande.

```bash
usermod -l studio -d /home/studio -m jarvis
getent passwd studio
id studio
```

Si `jarvis` était **le groupe privé du compte**, exécute
`groupmod -n studio jarvis` et vérifie de nouveau `id studio`. Le numéro de
groupe doit rester le même. Si d’autres comptes utilisent ce groupe, vérifie
leurs dépendances avant d’en changer le nom.

```bash
hostnamectl set-hostname lab-studio
sudoedit /etc/hosts
```

Dans `/etc/hosts`, remplace l’ancien hostname sur la ligne locale, typiquement
`127.0.1.1`. Vérifie `hostname` et `getent hosts lab-studio`. Si tu as repéré
une règle SSH ou sudo qui nomme le compte, remplace ce nom dans la règle avant
les tests. Utilise `visudo` pour sudoers. Vérifie la configuration SSH avec
`sshd -t` avant `systemctl reload ssh` si elle a changé.

Si une crontab était en place, révise ses chemins `/home/jarvis`, puis
réinstalle la copie revue avec `crontab -u studio "$backup/crontab.jarvis"`.
Vérifie aussi les scripts personnels et `~/.ssh/config` s’ils utilisaient
des chemins absolus sous l’ancien home. La clé publique utilisée pour entrer
sur la tour doit être présente dans `/home/studio/.ssh/authorized_keys`.

## 3. Tester l’accès et remettre le satellite en service

**Depuis Windows**, ouvre une nouvelle session avec `ssh lab-studio`.
Dans cette session, `whoami` doit afficher `studio`, `hostname` doit afficher
`lab-studio` et `sudo -v` doit réussir avec le mot de passe Linux de `studio`.
Pour continuer à te connecter à l’ancien compte avant la bascule, utilise
`ssh -l jarvis lab-studio`.

**Depuis WSL**, dans le dossier d’apprentissage et avec l’environnement
Ansible activé :

```bash
ansible -i inventory.yml lab-studio -m ansible.builtin.ping
```

Si le satellite Wyoming était installé, envoie son unité mise à jour
**depuis PowerShell**, à la racine du dépôt :

```powershell
scp .\deploiement\lab-studio\wyoming-satellite.service lab-studio:wyoming-satellite.service
```

**Dans la session Linux de `studio`**, recrée son environnement Python avant
de relancer l’unité. Déplace l’ancien `.venv` pour le conserver en cas de retour
en arrière. `script/setup` reconstruit les dépendances au nouveau chemin.

```bash
cd ~/wyoming-satellite
# Exécuter la ligne suivante seulement si .venv existe.
mv -- .venv ".venv.avant-renommage.$(date +%s)"
script/setup
```

Après la réussite de `script/setup`, sous `studio` :

```bash
sudo install -o root -g root -m 0644 ~/wyoming-satellite.service /etc/systemd/system/wyoming-satellite.service
sudo systemctl daemon-reload
sudo systemctl start wyoming-satellite.service
sudo systemctl is-active wyoming-satellite.service
```

Vérifie ensuite les services existants avec `sudo docker ps`. Si le clone
`~/homelab` accède au NAS, vérifie sa destination Git depuis la tour.

```bash
git -C ~/homelab remote get-url origin
ssh -G nas | grep -E '^(hostname|user|identityfile) '
```

Si l’URL utilise l’alias `nas`, mets son `HostName` à `192.168.50.198` dans
`~/.ssh/config`. Conserve le compte distant et la clé dédiée au NAS. Mets à
jour le chemin de la clé s’il pointe encore vers `/home/jarvis`. Si l’URL
contient directement l’ancienne IP `192.168.1.80`, remplace cette IP dans
`origin` en conservant le compte et le chemin du dépôt.

```bash
git -C ~/homelab ls-remote origin HEAD
```

### Créer l’accès Git de lab-studio avec agent0

Sur le NAS, `agent0` est le compte Git de la tour. Le rôle Ansible le crée
dans le groupe `agents` et lui donne le shell `git-shell`. Le compte
`studio` continue de servir à l’administration de la tour.

Depuis **WSL**, dans `ansible` avec ton environnement Ansible
activé, récupère la clé publique que la tour utilise pour le NAS. La clé
privée correspondante reste sur la tour.

```bash
cle_agent0=$(ssh -i ~/.ssh/id_ed25519_jarvis_central studio@192.168.50.252 'cat ~/.ssh/id_ed25519_nas.pub') &&
  printf '%s\n' "$cle_agent0" > roles/nas/files/agent0.pub
```

Applique le tag qui gère le montage et l’accès Git. Le mot de passe
**BECOME** est celui de `pinas`. **Vault password** déchiffre les variables
du NAS. Le rôle vérifie la lecture des quatre dépôts sous l’identité
`agent0` avant d’autoriser la clé.

```bash
ansible-playbook -i inventory.yml configurer-nas.yml --tags git-agents \
  --ask-become-pass --ask-vault-pass
```

Sur **lab-studio**, mets à jour le bloc existant dans `~/.ssh/config`.

```sshconfig
Host nas
    HostName 192.168.50.198
    User agent0
    IdentityFile /home/studio/.ssh/id_ed25519_nas
    IdentitiesOnly yes
```

Si `origin` utilise déjà `nas:/srv/git/homelab.git`, il suffit de relancer
le test Git. Si l’URL indique encore explicitement `jarvisc`, remplace-la
par l’alias.

```bash
git -C ~/homelab remote set-url origin nas:/srv/git/homelab.git  # Seulement si nécessaire.
git -C ~/homelab ls-remote origin HEAD
```

## 4. Basculer le compte de téléchargement du registry

**Depuis WSL**, dans le dossier d’apprentissage, applique uniquement le
montage du NVMe et le registry. Le rôle ajoute le compte de lecture
`lab-studio` avec le mot de passe de lecture déjà chiffré dans Vault.
L’ancien compte reste disponible pendant le test.

```bash
ansible-playbook -i inventory.yml configurer-nas.yml --tags registry \
  --ask-become-pass --ask-vault-pass
```

Ici, **BECOME password** est le mot de passe sudo de `pinas` sur le NAS.
**Vault password** est le mot de passe qui déchiffre les variables Ansible.

**Sur lab-studio**, utilise le mot de passe du **compte de lecture du registry**
pour `docker login`. Le test spécifie ARM64 parce que c’est la plateforme
de l’image de test déjà publiée sur le NAS.

```bash
sudo docker login 192.168.50.198:5001 --username lab-studio &&
  sudo docker pull --platform linux/arm64 192.168.50.198:5001/test/hello-world:tls
```

Quand le login et le pull réussissent, **depuis WSL**, retire l’ancien
identifiant. Ansible redéploie le conteneur de lecture avec le fichier
d’authentification mis à jour.

```bash
ansible-playbook -i inventory.yml configurer-nas.yml --tags registry \
  --ask-become-pass --ask-vault-pass \
  -e '{"registry_remove_legacy_reader": true}'
```

Refais le pull depuis la tour. Le compte de publication du NAS utilise
toujours le port 5000 et possède son propre mot de passe.

## 5. Clore la bascule

Quand SSH, sudo, Ansible et les services répondent, quitte le shell root
et la session `migration-studio`. Depuis une session `studio`, retire
le compte temporaire avec `sudo deluser migration-studio`. Cette commande
conserve son dossier personnel.

Si un contrôle échoue, garde la console de secours ouverte. Elle permet de
corriger la règle SSH ou sudo, de restaurer les fichiers de configuration
sauvegardés et, si nécessaire, de refaire le renommage dans l’autre sens
après avoir fermé les sessions de `studio`.

Références pour les opérations locales. [Manuel de usermod](https://manpages.debian.org/trixie/passwd/usermod.8.en.html) · [Environnements virtuels Python](https://docs.python.org/fr/3/library/venv.html)

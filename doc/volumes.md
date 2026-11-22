# Volumes

Chaque machine a son propre `/srv` : c’est l’emplacement prévu par Linux pour les données des services de la machine. Le `/srv` du NAS et celui de `lab-studio` sont donc deux dossiers distincts, sur deux disques différents. Le matériel de stockage est décrit dans [Machines](machines.md).

## NAS — le NVMe monté sur `/srv`

Sur le NAS, `/srv` n’est pas un simple dossier de la microSD : c’est le point de montage du NVMe de données. Toutes les données du NAS y sont, le système reste sur la microSD.

### Montage

Le [rôle data_disk](../ansible/roles/data_disk/tasks/main.yml) monte le disque et inscrit le montage dans `/etc/fstab` :

| Réglage | Valeur | Raison |
|---|---|---|
| Source | `UUID=<data_disk_uuid>` | L’UUID identifie le système de fichiers lui-même. Un nom comme `/dev/nvme0n1p1` peut changer selon l’ordre de détection des disques |
| Point de montage | `/srv` | |
| Système de fichiers | `ext4` | Système de fichiers existant sur le NVMe, Ansible ne le formate pas |
| Options | `defaults,nofail` | `nofail` laisse le Pi démarrer si le disque manque, pour garder l’accès SSH et réparer |

L’UUID attendu est déclaré dans les [variables NAS](../ansible/host_vars/nas/main.yml) (`data_disk_uuid`).

### Protection des services

Avec `nofail`, le Pi peut démarrer sans le NVMe. `/srv` serait alors un dossier vide de la microSD, et un service qui y écrirait remplirait la microSD au lieu du disque de données. Pour l’éviter, chaque service listé dans `data_disk_dependent_services` (Samba, containerd et Docker) reçoit un complément systemd `data-disk.conf` ([modèle](../ansible/roles/data_disk/templates/data-disk.conf.j2)) :

| Directive | Effet |
|---|---|
| `RequiresMountsFor=/srv` | Le service attend le montage de `/srv` avant de démarrer |
| `AssertPathIsMountPoint=/srv` | Le service refuse de démarrer si `/srv` n’est pas un point de montage |
| `ExecStartPre=findmnt … --source UUID=…` | Le service refuse de démarrer si le disque monté n’est pas le NVMe attendu |

Docker et containerd stockent aussi leurs propres données sur le NVMe : `data-root` vaut `/srv/docker` et `root` vaut `/srv/containerd` ([rôle Docker](../ansible/roles/docker/tasks/main.yml)).

### Vérifier le montage

Depuis le NAS :

```bash
findmnt --mountpoint /srv
```

Depuis le dossier `ansible/` sous WSL, le playbook [`lire-nas.yml`](../ansible/diagnostics/lire-nas.yml) compare l’UUID monté à celui des variables :

```bash
ansible-playbook -i inventory.yml diagnostics/lire-nas.yml --ask-vault-pass
```

### Inventaire

| Chemin | Contenu | Propriétaire et droits | Géré par |
|---|---|---|---|
| `/srv/partages` | Dossier parent des partages Samba | `root`, `0755` | [rôle samba](../ansible/roles/samba/tasks/main.yml) |
| `/srv/partages/<dossier>` | Espace personnel d’un compte, un par entrée de `samba_users` | le compte, `0700` | rôle samba |
| `/srv/samba` | Base des comptes Samba (`passdb`) et état du service | Samba | [`smb.conf`](../ansible/roles/samba/templates/smb.conf.j2) |
| `/srv/git` | Dépôts Git bare listés dans `git_server_repositories` | `pinas:agents`, `2750` | [rôle git_server](../ansible/roles/git_server/tasks/main.yml) |
| `/srv/registry` | Projet Compose du registry | `root`, `0755` | [rôle registry](../ansible/roles/registry/tasks/main.yml) |
| `/srv/registry/auth` | Comptes de publication (`htpasswd`) | `root`, `0700` | rôle registry |
| `/srv/registry/reader-auth` | Comptes de téléchargement (`htpasswd`) | `root`, `0700` | rôle registry |
| `/srv/registry/tls` | Clé privée et certificat HTTPS | `root`, `0700` | rôle registry |
| `/srv/registry/registry.crt` | Copie publique du certificat, lue par les clients | `root`, `0644` | rôle registry |
| `/srv/appdata/registry` | Images publiées | `root`, `0755` | rôle registry |
| `/srv/docker` | Données du moteur Docker | `root`, `0710` | [rôle Docker](../ansible/roles/docker/tasks/main.yml) |
| `/srv/containerd` | Données de containerd | `root`, `0700` | rôle Docker |

La remise en service du NAS et l’état des sauvegardes sont décrits dans [Exploitation](exploitation.md#remettre-le-nas-en-service).

## lab-studio — `/srv` sur le disque système

Sur la tour, `/srv` est un dossier du disque système : aucun disque dédié n’y est monté par Ansible. Le stockage de la tour reste à relever dans [Machines](machines.md).

### Inventaire

| Chemin | Contenu | Droits | Géré par |
|---|---|---|---|
| `/srv/compose/ollama` | Projet Compose `ollama` : `compose.yml` et ses sauvegardes | `root`, `0755` | [rôle ollama](../ansible/roles/ollama/tasks/main.yml) |
| `/srv/compose/home-assistant` | Projet Compose `home-assistant` : `compose.yml` et ses sauvegardes | `root`, `0755` | [rôle home_assistant](../ansible/roles/home_assistant/tasks/main.yml) |
| `/srv/homeassistant` | Configuration et données de Home Assistant, montée sur `/config` | conservés tels quels | rôle home_assistant, conteneur `homeassistant` |
| `/srv/wyoming/whisper` | Modèles de Whisper, montés sur `/data` | conservés tels quels | rôle home_assistant, conteneur `whisper` |
| `/srv/wyoming/piper` | Voix de Piper, montées sur `/data` | conservés tels quels | rôle home_assistant, conteneur `piper` |
| Volume Docker `ollama` | Modèles Ollama, montés sur `/root/.ollama` | Docker | Volume externe préservé par le rôle ollama |
| `/home/studio/wyoming-satellite` | Clone et environnement Python du satellite | `studio` | [rôle wyoming_satellite](../ansible/roles/wyoming_satellite/tasks/main.yml) |

Ansible crée les dossiers de données s’ils manquent, mais ne modifie pas leurs droits : les conteneurs y écrivent avec leurs propres comptes. Seuls les dossiers sous `/srv/compose`, qui ne contiennent que la configuration Compose, reçoivent des droits fixés.

Le volume `ollama` est stocké dans le dossier de données de Docker, à son emplacement par défaut : le rôle Docker de la tour ne le déplace pas. Avant chaque déploiement, les rôles `ollama` et `home_assistant` vérifient que les conteneurs existants appartiennent bien à leur projet Compose et utilisent les mêmes dossiers ou volumes de données. Ils s’arrêtent en cas d’écart.

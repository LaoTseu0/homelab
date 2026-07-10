# Installation du serveur dédié Jarvis

> Comment monter le serveur dédié qui héberge Jarvis : OS headless, drivers
> GPU, Docker et accès GPU depuis les conteneurs
> (vieux PC gamer — RTX 2060 6 Go, 32 Go RAM, Ryzen 5).
> Correspond au début de la **Phase 0** de [jarvis-maison-architecture.md](jarvis-maison-architecture.md).
> Dernière mise à jour : 10 juillet 2026
> Statut : **socle opérationnel** (OS + GPU + Docker + accès GPU conteneurs validé)

---

## 1. Vue d'ensemble

Le PC a été formaté (Windows supprimé) et transformé en serveur Linux headless,
administré en SSH depuis le PC principal, comme le NAS.

| Élément | Valeur |
|---|---|
| OS | Ubuntu Server **26.04 LTS** (support jusqu'en 2031) |
| Hostname | `jarvis-central` |
| Utilisateur | `jarvis` |
| Accès | SSH (écran/clavier débranchés après installation) |
| GPU | NVIDIA RTX 2060 6 Go — visible depuis l'hôte **et** depuis les conteneurs |

**Choix d'architecture** (répond à la question ouverte n°2 du doc Jarvis) :
Ubuntu Server + **Docker**, plutôt que Proxmox/HAOS en VM. On perd les add-ons
clé-en-main de Home Assistant OS, mais chaque brique (HA, Ollama, Whisper,
Piper…) devient un simple conteneur — plus aligné avec la démarche
« une brique testable à la fois ».

---

## 2. Installation de l'OS

1. Clé USB bootable créée avec **Rufus** (PC principal) à partir de l'ISO
   Ubuntu Server 26.04 LTS.
2. Installation avec écran + clavier branchés **temporairement** (contrairement
   au Pi, pas de pré-configuration headless possible sur un PC classique).
3. Point important pendant l'installation : cocher **`[X] Install OpenSSH server`**
   à l'écran « SSH Setup » → le serveur SSH est actif dès le premier démarrage.
4. Après vérification de la connexion SSH depuis le PC principal : écran et
   clavier débranchés, la machine tourne en headless.

> Réglage BIOS recommandé : « Restore on AC Power Loss » → **Power On**
> (redémarrage automatique après coupure de courant, indispensable en headless).

---

## 3. Commandes exécutées

### 3.1 Mise à jour du système

```bash
sudo apt update && sudo apt full-upgrade -y
```

Met à jour la liste des paquets (`update`) puis installe toutes les mises à
jour disponibles, y compris le noyau (`full-upgrade`).

### 3.2 Drivers NVIDIA

```bash
sudo ubuntu-drivers install
sudo reboot
```

`ubuntu-drivers` détecte le GPU et installe automatiquement le driver NVIDIA
propriétaire recommandé. Le reboot est nécessaire pour charger le nouveau
module noyau.

**Vérification** (après reconnexion SSH) :

```bash
nvidia-smi
```

Doit afficher un tableau avec la **GeForce RTX 2060**, la version du driver et
**6144 MiB** de VRAM. ✅ Validé.

### 3.3 Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

- La première commande télécharge et exécute le script d'installation officiel
  de Docker (ajoute le dépôt Docker et installe le moteur).
- `usermod -aG docker` ajoute l'utilisateur `jarvis` au groupe `docker`, ce qui
  permet de lancer des conteneurs **sans sudo**. Nécessite de se déconnecter /
  reconnecter (SSH) pour prendre effet.

**Vérification** :

```bash
docker run --rm hello-world
```

### 3.4 NVIDIA Container Toolkit (pont GPU → conteneurs)

```bash
# Clé de signature du dépôt NVIDIA
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

# Ajout du dépôt (en le liant à la clé ci-dessus)
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Installation
sudo apt update && sudo apt install -y nvidia-container-toolkit

# Configuration de Docker pour utiliser le runtime NVIDIA
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

- Les deux `curl` ajoutent le dépôt apt officiel de NVIDIA avec sa clé de
  signature (le `sed` insère la référence à la clé dans la ligne du dépôt).
- `nvidia-ctk runtime configure` modifie `/etc/docker/daemon.json` pour
  déclarer le runtime NVIDIA auprès de Docker.
- Le redémarrage de Docker applique cette configuration.

**Vérification finale** — un conteneur qui voit le GPU :

```bash
docker run --rm --gpus all ubuntu nvidia-smi
```

Affiche le même tableau que le `nvidia-smi` de l'hôte → le GPU est accessible
depuis les conteneurs. ✅ Validé.

> L'état final du socle et les services qui tournent dessus sont décrits dans
> [jarvis-body.md](jarvis-body.md).

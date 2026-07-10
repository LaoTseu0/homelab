# NAS — installation et configuration

> Procédures : comment le NAS a été monté (système, SSH, serveur git, Samba).
> Le pourquoi et le modèle d'accès sont dans
> [../../architecture/nas.md](../../architecture/nas.md).
> Dernière mise à jour : 10 juillet 2026

---

## 1. Système

- **OS** : Raspberry Pi OS Lite (64-bit), installé en mode *headless*
  (pré-configuration via Raspberry Pi Imager).
- **Hostname** : `nas`
- **Utilisateur administrateur** : `pinas`
- Système mis à jour (`apt update && apt full-upgrade`).

---

## 2. Accès SSH

- Connexion par **clé SSH** (ed25519) depuis le PC principal.
- La clé du NAS est **distincte** de la clé GitHub (pas de mélange).
- Authentification par **mot de passe conservée** en secours (pour brancher
  d'autres PC / futurs agents tant qu'ils n'ont pas leur propre clé).

### Côté PC — fichier `~/.ssh/config`

```
Host nas
    HostName nas.local
    User pinas
    IdentityFile C:\Users\Lao\.ssh\id_ed25519_nas
    IdentitiesOnly yes
```

Connexion simplifiée : `ssh nas`

> Depuis une **machine** (config de service, script) : utiliser l'IP du NAS
> plutôt que `nas.local` — convention et adresses dans
> [../../architecture/reseau.md](../../architecture/reseau.md).

---

## 3. Serveur git

### Emplacement des dépôts

Tous les dépôts nus vivent dans :

```
/srv/git/
```

### Modèle de permissions

- Le dossier `/srv/git` **appartient à `pinas`** (propriétaire) et au groupe `agents`.
- Permissions `2775` :
  - propriétaire et groupe `agents` peuvent lire / écrire / accéder,
  - le bit **setgid** (`2`) fait hériter le groupe `agents` à tout nouveau contenu.
- Conséquence : **seul `pinas` peut créer ou supprimer des dépôts** (il possède le
  dossier parent), tandis que les membres du groupe `agents` peuvent travailler
  *dans* les dépôts.

### Réglage multi-comptes

Chaque dépôt est configuré en dépôt partagé de groupe :

```
git config core.sharedRepository group
```

Cela évite les conflits de permissions quand plusieurs comptes poussent dans le
même dépôt.

### Branche par défaut

Configuré (en tant que `pinas`) pour que tout nouveau dépôt parte sur `main` :

```bash
git config --global init.defaultBranch main
```

> Historique : `memoire-agent.git` avait été créé sur `master` (ancien défaut
> de git). Rectifié le 10 juillet 2026 :
>
> ```bash
> git -C /srv/git/memoire-agent.git branch -m master main
> git -C /srv/git/memoire-agent.git symbolic-ref HEAD refs/heads/main
> ```
>
> (et sur chaque clone existant : `git branch -m master main`, `git fetch`,
> `git branch -u origin/main main`, `git remote set-head origin -a`.)

### Créer un nouveau dépôt (procédure standard)

```bash
# 1. Sur le PC — le dépôt de travail
cd mon-app
git init
git add . && git commit -m "Premier commit"

# 2. Sur le NAS — le dépôt central (une seule fois, en tant que pinas)
ssh nas "git init --bare --shared=group /srv/git/mon-app.git"

# 3. Sur le PC — relier et pousser
git remote add origin nas:/srv/git/mon-app.git
git push -u origin main
```

Le point clé de l'étape 2 : **`--shared=group`** règle
`core.sharedRepository=group` **et** les permissions de groupe dès la
création. Combiné au setgid de `/srv/git`, le dépôt naît conforme au modèle
d'accès (groupe `agents`), sans retouche manuelle.
`git init --bare` ne s'utilise **que** sur le NAS — jamais sur un poste de
travail.

### Dépôts existants (vérifié le 10 juillet 2026)

- `memoire-agent.git` — mémoire des agents (dépôt de test initial).
- `homelab.git` — ce dépôt (doc + config de déploiement du homelab).

### Adresse de clonage (depuis un poste autorisé)

```
git clone nas:/srv/git/<nom-du-depot>.git
```

---

## 4. Partage de fichiers (SMB / Samba)

- Service **Samba** (`smbd`) installé et actif.
- Utilisateur **`oce`** (Océane), compte Linux **sans accès shell**
  (`/usr/sbin/nologin`) : accès **uniquement** via SMB, jamais au système.
- Mot de passe Samba dédié (géré par `smbpasswd`, distinct du mot de passe Linux).

### Dossier partagé

```
/srv/partages/oceane    (propriétaire oce:oce, permissions 700)
```

Cloisonné : seul `oce` y a accès.

### Bloc de configuration (`/etc/samba/smb.conf`)

```ini
[Oceane]
   path = /srv/partages/oceane
   valid users = oce
   read only = no
   browseable = yes
   create mask = 0600
   directory mask = 0700
```

### Accès client

- **PC Windows** : `\\<IP-du-Pi>\Oceane` (identifiants `oce`).
- **Android** : appli de fichiers compatible SMB (ex. « Mes fichiers » Samsung),
  hôte = IP du Pi, port = **445**, utilisateur `oce`.
- Le client doit être sur le **WiFi de la maison** (accès local uniquement).

# NAS — installation et configuration

> Procédures : comment le NAS a été monté (système, SSH, serveur git,
> miroir GitHub, Samba).
> Le pourquoi et le modèle d'accès sont dans
> [../../architecture/nas.md](../../architecture/nas.md).
> Dernière mise à jour : 24 juillet 2026

---

## 1. Système

- **OS** : Raspberry Pi OS Lite (64-bit), installé en mode *headless*
  (pré-configuration via Raspberry Pi Imager).
- **Hostname** : `nas`
- **Utilisateur administrateur** : `pinas`
- Système mis à jour (`apt update && apt full-upgrade`).

---

## 2. Accès SSH

- Connexion par **clé SSH** (ed25519) depuis `pc-admin`.
- La clé du NAS est **distincte** de la clé GitHub (pas de mélange).
- Authentification par **mot de passe conservée** en secours (pour brancher
  d'autres PC / futurs agents tant qu'ils n'ont pas leur propre clé).

### Côté pc-admin — fichier `~/.ssh/config`

```
Host nas
    HostName 192.168.1.80
    User pinas
    IdentityFile C:\Users\antho\.ssh\id_ed25519_nas
    IdentitiesOnly yes
```

Connexion simplifiée : `ssh nas`

> Convention (détail dans [../pc-admin/installation.md](../pc-admin/installation.md)) :
> l'alias `Host` porte le **nom de la machine** (`nas`), le compte est dans
> `User` (`pinas`), la clé est nommée `id_ed25519_<machine>`. Depuis une
> **machine** (config de service, script) : utiliser l'IP directement —
> convention et adresses dans
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
>
> Même famille de problème sur `homelab.git` : créé avec un HEAD pointant
> sur `master` alors que seule `main` a été poussée. **Symptôme** : un clone
> frais arrive **vide** avec `warning: remote HEAD refers to nonexistent
> ref, unable to checkout`. **Correction** (rectifié le 10 juillet 2026) :
>
> ```bash
> sudo git -C /srv/git/homelab.git symbolic-ref HEAD refs/heads/main
> # puis dans le clone déjà fait : git checkout main
> ```

### Confiance multi-comptes (`safe.directory`)

Depuis git 2.35.2 (CVE-2022-24765), git refuse d'opérer dans un dépôt
appartenant à **un autre utilisateur** — les permissions Unix n'y changent
rien : elles disent qui *peut* accéder, `safe.directory` dit à qui l'on
*fait confiance* (un dépôt piégé peut exécuter du code via hooks/config).
Notre modèle « dépôts de `pinas`, utilisés par le groupe `agents` » est
l'usage légitime prévu : on déclare la confiance au niveau **système**,
une fois par dépôt :

```bash
sudo git config --system --add safe.directory /srv/git/homelab.git
sudo git config --system --add safe.directory /srv/git/memoire-agent.git
```

**Symptôme si on l'oublie** : `fatal: detected dubious ownership in
repository` au clone/pull depuis un compte agent.

### Créer un nouveau dépôt (procédure standard)

```bash
# 1. Sur le PC — le dépôt de travail
cd mon-app
git init
git add . && git commit -m "Premier commit"

# 2. Sur le NAS — le dépôt central (une seule fois, en tant que pinas)
ssh nas "git init --bare --shared=group /srv/git/mon-app.git"
ssh nas "sudo git config --system --add safe.directory /srv/git/mon-app.git"

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

### Inspecter un dépôt bare sans le cloner

```bash
git -C /srv/git/<depot>.git ls-tree -r --name-only main   # liste des fichiers
git -C /srv/git/<depot>.git log --oneline -5              # derniers commits
```

---

## 4. Miroir GitHub (hook `post-receive`)

> Le pourquoi et le modèle (NAS = source de vérité, GitHub = copie) sont dans
> [../../architecture/nas.md](../../architecture/nas.md) §4.
> Procédure écrite le 23 juillet 2026 — **à dérouler sur le NAS** (dater cette
> ligne « mis en place le … » une fois le test §4.6 concluant).

**Principe** : on ne pousse **jamais** vers GitHub depuis un poste de travail.
On pousse vers le NAS, et le NAS recopie vers GitHub. Le sens est
**unidirectionnel** : NAS → GitHub. GitHub n'est qu'une copie consultable
(et une sauvegarde hors-site de fait).

Un dépôt bare peut avoir des remotes comme n'importe quel dépôt : c'est ce qui
rend la mécanique possible.

### 4.1 Clé SSH dédiée du NAS

Le NAS a besoin de sa propre identité pour pousser vers GitHub. Convention
maison (`id_ed25519_<destination>`), **sans passphrase** — le hook s'exécute
sans humain devant :

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_github -N "" -C "nas -> github"
cat ~/.ssh/id_ed25519_github.pub
```

Cette clé publique se déclare côté GitHub en **Deploy Key du dépôt concerné,
avec la case « Allow write access »** — pas en clé de compte : une Deploy Key
n'ouvre l'accès qu'à **ce dépôt-là**. Si le NAS est compromis, le rayon
d'explosion se limite à ce miroir.

`Settings` du dépôt → `Deploy keys` → `Add deploy key` → coller la clé,
cocher *Allow write access*.

Puis déclarer l'hôte dans `~/.ssh/config` de `pinas` :

```
Host github.com
    HostName github.com
    User git
    IdentityFile /home/pinas/.ssh/id_ed25519_github
    IdentitiesOnly yes
```

Enregistrer l'empreinte du serveur GitHub **avant** le premier hook (un hook
est non-interactif : il ne peut pas répondre « yes » à la question de
confiance) :

```bash
ssh-keyscan github.com >> ~/.ssh/known_hosts
ssh -T git@github.com    # doit répondre : Hi <depot>! You've successfully authenticated...
```

**Symptôme si on l'oublie** : `Host key verification failed.` dans la sortie
du `git push` du poste de travail — le push vers le NAS réussit quand même
(voir §4.5).

### 4.2 Ajouter GitHub comme remote sur le dépôt bare

Le dépôt GitHub doit exister et être **vide** (pas de README ni de licence
générés à la création : ils créeraient un historique divergent).

```bash
sudo -u pinas git -C /srv/git/homelab.git remote add github git@github.com:<compte>/homelab.git
sudo -u pinas git -C /srv/git/homelab.git remote -v
```

Le remote local du dépôt bare s'appelle `github` ; il n'entre pas en conflit
avec l'`origin` des clones (qui, lui, pointe vers le NAS).

### 4.3 Le hook `post-receive`

`post-receive` s'exécute **après** que les références ont été mises à jour dans
le dépôt bare. Git lui passe sur l'entrée standard une ligne par référence
poussée : `<ancien-sha> <nouveau-sha> <nom-de-la-ref>`.

Fichier `/srv/git/homelab.git/hooks/post-receive` :
Exécuter cette cmd dans le terminal pour garantir les fin de ligne Unix (LF). Pas de BOM.

```sh
cat > /srv/git/homelab.git/hooks/post-receive <<'EOF'
#!/bin/sh
# Miroir GitHub : recopie vers le remote "github" les refs mises a jour.
zero=$(git hash-object --stdin </dev/null | tr '0-9a-f' '0')
while read -r oldrev newrev refname
do
    if [ "$newrev" = "$zero" ]; then
        git push github --delete "$refname" || echo "Miroir: echec suppression $refname"
    else
        git push github "$refname:$refname" || echo "Miroir: echec push $refname"
    fi
done
EOF
```

Le rendre exécutable :

```bash
sudo chmod +x /srv/git/homelab.git/hooks/post-receive
sudo chown pinas:agents /srv/git/homelab.git/hooks/post-receive
```

**Pourquoi cette forme plutôt que `git push github --all && git push github --tags`** :

- on ne pousse que les références **réellement modifiées** par ce push, au lieu
  de rejouer toutes les branches à chaque fois ;
- `refname:refname` couvre d'un seul geste les **branches** (`refs/heads/…`)
  **et** les **tags** (`refs/tags/…`) — pas besoin d'un `--tags` séparé ;
- une branche supprimée sur le NAS est supprimée sur GitHub : le miroir reste
  fidèle à la source de vérité, sinon GitHub accumulerait des branches mortes.

> Variante non retenue : `git push github --mirror`, qui aligne GitHub sur le
> NAS d'un bloc (suppressions comprises). Plus radical — il écrase **tout** ce
> qui existe côté GitHub, y compris une référence créée par erreur depuis
> l'interface web. À réserver à une resynchronisation manuelle.

### 4.4 Qui exécute le hook — la limite à connaître

Le hook tourne sous **le compte Unix qui a poussé**, pas sous un compte de
service. La clé GitHub vivant dans `/home/pinas/.ssh/` (permissions `600`),
le miroir ne fonctionne donc aujourd'hui **que pour les pushes faits en tant
que `pinas`** — ce qui couvre les postes humains (`pc-admin` se connecte en
`pinas`).

**Symptôme le jour où un compte du groupe `agents` poussera** :
`git@github.com: Permission denied (publickey)` dans la sortie du push, le
dépôt NAS étant à jour malgré tout.

Rendre la clé lisible par le groupe n'est pas une bonne réponse : elle donnerait
à tous les agents un droit d'écriture sur GitHub, et `ssh` refuse de son côté une
clé privée trop permissive quand son propriétaire s'en sert (`UNPROTECTED PRIVATE
KEY FILE`). La piste propre, le moment venu : le hook dépose un marqueur, et une
unité systemd tournant en `pinas` fait le push. Suivi dans
[../../backlog.md](../../backlog.md).

### 4.5 Ce qui se passe si GitHub est injoignable

Rien de grave, **par construction** : `post-receive` s'exécute *après* la mise à
jour des références. Son code de retour ne peut plus annuler le push. Une panne
GitHub, une clé expirée ou une coupure Internet produisent un message d'erreur
dans la sortie du `git push` du poste de travail, mais **le NAS a bien reçu le
commit**. La source de vérité n'est jamais otage du miroir.

Pour rattraper un miroir en retard :

```bash
sudo -u pinas git -C /srv/git/homelab.git push github --all
sudo -u pinas git -C /srv/git/homelab.git push github --tags
```

### 4.6 Tester

Depuis un poste de travail, un push normal :

```bash
git push origin main
```

La sortie doit afficher les lignes du remote (`remote: To github.com:…`), et le
commit apparaître sur GitHub dans la foulée. Vérification côté NAS :

```bash
sudo -u pinas git -C /srv/git/homelab.git ls-remote github main
```

---

## 5. Partage de fichiers (SMB / Samba)

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

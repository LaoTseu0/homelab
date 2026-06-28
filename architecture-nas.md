# Architecture NAS maison

> Documentation de l'installation NAS auto-hébergée.
> Dernière mise à jour : 28 juin 2026
> Statut : **phase de test** (stockage sur microSD, backup SSD à venir)

---

## 1. Vue d'ensemble

NAS auto-hébergé sur Raspberry Pi, destiné à deux usages :

- **Serveur git** pour héberger la mémoire des agents (fichiers `.md` versionnés).
- **Partage de fichiers (SMB)** pour un usage familial (photos, documents).

Accès **local uniquement** pour l'instant (pas d'exposition à Internet). Un accès
distant via VPN pourra être ajouté plus tard.

---

## 2. Matériel

| Élément | Détail | Rôle actuel |
|---|---|---|
| Raspberry Pi 4 Model B | 8 Go de RAM | Machine du NAS |
| microSD | — | OS **et** données (stockage primaire, **phase de test**) |
| SSD Kingston 250 Go (SATA) | nécessite un adaptateur USB-SATA (à acheter) | Backup (prévu, pas encore en place) |
| NVMe 1 To | format M.2 / PCIe | Mis de côté pour un autre projet |
| Raspberry Pi 5 8 Go | — | Réservé à d'autres projets |
| Routeur Asus RT-AX86U Pro | non branché | Réservé à un projet futur (VPN, etc.) |

> Réseau actuel : box Free, connexion **Ethernet** du Pi.

---

## 3. Système

- **OS** : Raspberry Pi OS Lite (64-bit), installé en mode *headless*.
- **Hostname** : `nas`
- **Utilisateur administrateur** : `pinas`
- Système mis à jour (`apt update && apt full-upgrade`).

---

## 4. Accès SSH

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

---

## 5. Serveur git

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

### Dépôts existants

- `memoire-agent.git` — mémoire des agents (dépôt de test initial).
- `archi-maison.git` — documentation de l'architecture (ce dossier).

### Adresse de clonage (depuis un poste autorisé)

```
git clone nas:/srv/git/<nom-du-depot>.git
```

---

## 6. Partage de fichiers (SMB / Samba)

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

---

## 7. Modèle d'accès — résumé

| Qui | Outil | Accès |
|---|---|---|
| `pinas` (admin) | SSH (clé) + sudo | Tout : système, dépôts git, création/suppression |
| Agents | git via SSH (groupe `agents`) | Travail dans les dépôts, pas de gestion |
| `oce` (Océane) | SMB | Uniquement son dossier `/srv/partages/oceane` |

Les deux mondes (git technique / partage familial) sont **cloisonnés** : comptes
distincts, dossiers distincts, mécanismes distincts.

---

## 8. À faire / prochaines étapes

- [ ] Acheter un **adaptateur USB-SATA** pour le SSD Kingston.
- [ ] Mettre en place le **backup automatique** (rsync + cron) des données
      (dépôts git + dossier Océane) vers le SSD.
- [ ] (Plus tard) Migrer le stockage primaire de la microSD vers un disque plus
      durable.
- [ ] (Optionnel) Clés SSH dédiées par agent + comptes Linux par agent si besoin
      de cloisonner les droits entre agents.
- [ ] (Optionnel) Accès distant via VPN (routeur Asus RT-AX86U Pro).
- [ ] (Optionnel) Passphrase sur la clé SSH du PC principal.

---

## 9. Points de vigilance

- **Sauvegarde** : tant que le backup n'est pas en place, toutes les données
  vivent sur la **seule microSD**. Les dépôts git sont protégés s'ils sont clonés
  ailleurs (PC), mais **les fichiers d'Océane ne le sont pas** — priorité au backup.
- **microSD en 24/7** : usure possible à terme ; le passage à un SSD est prévu.
- **VPN du PC** : doit être **désactivé** pour administrer le NAS en local.

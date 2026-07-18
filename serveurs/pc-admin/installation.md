# pc-admin — installation du poste d'administration

> Comment le PC portable Asus ROG (Windows, PC perso) est configuré pour
> administrer les machines du homelab en SSH par clé.
> Adresses IP : [../../architecture/reseau.md](../../architecture/reseau.md).
> Dernière mise à jour : 18 juillet 2026
> Statut : accès `nas` et `jarvis-central` en place ; `jarvis-core` à faire
> (compte à créer à l'installation de son socle)

---

## 1. Convention SSH du parc

Une paire de clés **par machine cible** (compromission d'une clé = un seul
accès à révoquer), et un nommage unique partout :

| Élément | Convention | Exemple |
|---|---|---|
| Alias `Host` | le **nom de la machine** (jamais le compte) | `nas` |
| `User` | le compte d'administration de la machine | `pinas` |
| Fichier de clé | `id_ed25519_<machine>` | `id_ed25519_nas` |

| Machine | Alias | User | IP |
|---|---|---|---|
| NAS | `nas` | `pinas` | 192.168.1.80 |
| Serveur Jarvis | `jarvis-central` | `jarvis` | 192.168.1.57 |
| Tour d'inférence | `jarvis-core` | *(à créer)* | 192.168.1.187 |

## 2. Créer une paire de clés (une par machine)

Dans un terminal PowerShell sur `pc-admin` :

```powershell
ssh-keygen -t ed25519 -C "pc-admin" -f C:\Users\antho\.ssh\id_ed25519_nas
```

- `-C "pc-admin"` : commentaire identifiant la provenance de la clé.
- `-f ...\id_ed25519_<machine>` : le nom de fichier suit la convention —
  sans `-f`, ssh-keygen proposerait le nom par défaut `id_ed25519` et
  écraserait la clé précédente.

Répéter pour chaque machine (`id_ed25519_jarvis-central`,
`id_ed25519_jarvis-core`).

## 3. Déclarer les alias — fichier `C:\Users\antho\.ssh\config`

```
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

- `IdentitiesOnly yes` : n'essaie que la clé déclarée (sans ça, ssh
  présente toutes les clés de l'agent, et certains serveurs coupent après
  trop de tentatives).
- ⚠️ Ces IP ne sont pas encore réservées sur la box (backlog) — si une
  machine devient injoignable, vérifier son bail DHCP.

## 4. Déposer la clé publique sur la machine cible

Pas de `ssh-copy-id` sous Windows — envoi manuel (le mot de passe du compte
est demandé une dernière fois) :

```powershell
type C:\Users\antho\.ssh\id_ed25519_nas.pub | ssh pinas@192.168.1.80 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

Répéter pour chaque machine avec sa clé et son compte.

## 5. Vérifier

```powershell
ssh nas
ssh jarvis-central
```

La connexion doit s'ouvrir **sans mot de passe**. C'est le prérequis pour
passer une machine en `PasswordAuthentication no`
(must-have n°3 de [../../architecture/securite.md](../../architecture/securite.md)).

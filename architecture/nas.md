# Architecture — NAS

> Ce que le NAS est, à quoi il sert, et son modèle d'accès.
> Les procédures d'installation détaillées sont dans
> [../serveurs/nas/installation.md](../serveurs/nas/installation.md).
> Dernière mise à jour : 23 juillet 2026
> Statut : **phase de test** (stockage sur microSD, backup SSD à venir)

---

## 1. Vue d'ensemble

NAS auto-hébergé sur Raspberry Pi, destiné à deux usages :

- **Serveur git** pour héberger la mémoire des agents et la doc du homelab
  (fichiers `.md` versionnés), avec **miroir sortant vers GitHub** (§4).
- **Partage de fichiers (SMB)** pour un usage familial (photos, documents).

Accès **local uniquement** (aucune exposition entrante depuis Internet). Un
accès distant via VPN pourra être ajouté plus tard.

---

## 2. Matériel

| Élément | Détail | Rôle actuel |
|---|---|---|
| Raspberry Pi 4 Model B | 8 Go de RAM | Machine du NAS |
| microSD | — | OS **et** données (stockage primaire, **phase de test**) |
| SSD Kingston 250 Go (SATA) | nécessite un adaptateur USB-SATA (à acheter) | Backup (prévu, pas encore en place) |
| NVMe 1 To | format M.2 / PCIe | Mis de côté pour un autre projet |
| Routeur Asus RT-AX86U Pro | branché, en répéteur derrière la box | Raccorde les machines filaires ; VLAN/VPN en projet futur (voir [reseau.md](reseau.md)) |

> Réseau actuel : box Bouygues, connexion **Ethernet** du Pi
> (voir [reseau.md](reseau.md)).

---

## 3. Le système git — serveur « bare over SSH »

Le NAS n'héberge **pas une forge** (GitHub, GitLab, Gitea…) : c'est du
**git natif servi par SSH**, la forme la plus élémentaire d'hébergement git
(modèle décrit dans le chapitre « Git on the Server » du livre Pro Git).
Trois concepts le définissent :

- **Dépôts bare** (« nus ») : les `*.git` de `/srv/git` ne contiennent que
  l'historique, pas de répertoire de travail. On ne travaille jamais dedans —
  on y pousse et on en tire (commandes d'inspection dans
  [../serveurs/nas/installation.md](../serveurs/nas/installation.md)).
- **SSH comme seul protocole** : un clone ouvre une connexion SSH et lance
  les commandes git côté Pi. Pas de démon dédié, pas de service web —
  SSH *est* le serveur.
- **Shared repository model** : `core.sharedRepository=group` + bit setgid
  sur `/srv/git` + groupe `agents` → les permissions Unix font office de
  gestion des droits multi-comptes. S'y ajoute la déclaration de confiance
  `safe.directory` (les permissions disent qui *peut* accéder, elle dit à
  qui l'on *fait confiance* — détail dans
  [../serveurs/nas/installation.md](../serveurs/nas/installation.md)).

**Pourquoi ce choix** : zéro maintenance, zéro surface d'attaque
supplémentaire (SSH était déjà là), et aligné avec la philosophie du projet
(git + markdown, pas de service superflu).

**Évolutions possibles si le besoin émerge** (aucune urgence) :
- une forge légère auto-hébergée (**Gitea/Forgejo**) si le besoin d'une
  interface web (relecture, navigation) apparaît ;
- **Gitolite** si la gestion des comptes Unix à la main devient pénible
  (droits fins par dépôt/branche).

---

## 4. Miroir GitHub — le NAS reste la source de vérité

Le NAS pousse ses dépôts vers GitHub, **jamais l'inverse**. GitHub n'est ni un
second serveur ni un lieu de travail : c'est une **copie en lecture**, utile
pour consulter le code hors du LAN, le partager ponctuellement, et — effet de
bord bienvenu tant que le backup n'existe pas — disposer d'un exemplaire
hors-site de l'historique.

```
[ poste de travail ]──push──►[ NAS  /srv/git/*.git ]──hook post-receive──►[ GitHub ]
       clone/pull ◄──────────  SOURCE DE VÉRITÉ                              miroir
                                                                        (lecture seule)
```

Trois propriétés définissent le montage :

- **Un seul sens.** On ne pousse jamais vers GitHub depuis un poste. Une
  modification faite via l'interface web serait écrasée ou ignorée au push
  suivant : il n'y a qu'une source de vérité, et elle est à la maison.
- **Déclenchement par hook.** Le dépôt bare exécute un hook `post-receive`
  après chaque push reçu, qui recopie vers GitHub les seules références
  modifiées. Aucun cron, aucune synchronisation périodique : le miroir suit le
  rythme des pushes.
- **Le miroir ne peut pas bloquer la source.** Le hook s'exécute *après* la
  mise à jour des références : GitHub injoignable produit un avertissement,
  jamais un push refusé. Le NAS fonctionne seul, exactement comme avant.

**Pourquoi pas l'inverse** (GitHub source, NAS miroir) : le homelab doit rester
opérationnel sans Internet, et sa doc appartient à la maison. Faire dépendre le
travail quotidien d'un service tiers contredirait le principe « 100 % local ».

**Ce que ça change côté posture** : le contenu des dépôts concernés **quitte le
LAN**. C'est le premier flux sortant du homelab — il ne crée aucune exposition
entrante, mais il impose deux règles : dépôts GitHub **privés**, et **aucun
secret** dans les dépôts miroités (voir [securite.md](securite.md)).

---

## 5. Modèle d'accès — résumé

| Qui | Outil | Accès |
|---|---|---|
| `pinas` (admin) | SSH (clé) + sudo | Tout : système, dépôts git, création/suppression |
| Agents | git via SSH (groupe `agents`) | Travail dans les dépôts, pas de gestion |
| `oce` (Océane) | SMB | Uniquement son dossier `/srv/partages/oceane` |

Les deux mondes (git technique / partage familial) sont **cloisonnés** : comptes
distincts, dossiers distincts, mécanismes distincts.

---

## 6. Points de vigilance

- **Sauvegarde** : tant que le backup n'est pas en place, toutes les données
  vivent sur la **seule microSD**. Les dépôts git sont protégés s'ils sont clonés
  ailleurs (PC) ou miroités sur GitHub (§4), mais **les fichiers d'Océane ne le
  sont pas** — priorité au backup.
- **Clé GitHub du NAS** : elle vit en clair sur la microSD (sans passphrase,
  contrainte d'un hook non-interactif). D'où le choix d'une **Deploy Key par
  dépôt** plutôt qu'une clé de compte : elle n'ouvre l'écriture que sur le
  dépôt miroité, pas sur l'ensemble du compte GitHub.
- **Miroir et comptes agents** : le hook s'exécute sous le compte qui pousse ;
  seul `pinas` dispose aujourd'hui de la clé GitHub. Les pushes des futurs
  comptes `agents` arriveront bien sur le NAS mais ne seront pas miroités tant
  que ce point n'est pas traité (détail et piste dans
  [../serveurs/nas/installation.md](../serveurs/nas/installation.md) §4.4).
- **microSD en 24/7** : usure possible à terme ; le passage à un SSD est prévu.
- **VPN du PC** : doit être **désactivé** pour administrer le NAS en local.

> Les tâches en attente (backup, migration SSD, VPN…) sont suivies dans
> [../backlog.md](../backlog.md).

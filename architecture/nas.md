# Architecture — NAS

> Ce que le NAS est, à quoi il sert, et son modèle d'accès.
> Les procédures d'installation détaillées sont dans
> [../serveurs/nas/installation.md](../serveurs/nas/installation.md).
> Dernière mise à jour : 10 juillet 2026
> Statut : **phase de test** (stockage sur microSD, backup SSD à venir)

---

## 1. Vue d'ensemble

NAS auto-hébergé sur Raspberry Pi, destiné à deux usages :

- **Serveur git** pour héberger la mémoire des agents et la doc du homelab
  (fichiers `.md` versionnés).
- **Partage de fichiers (SMB)** pour un usage familial (photos, documents).

Accès **local uniquement** (pas d'exposition à Internet). Un accès distant via
VPN pourra être ajouté plus tard.

---

## 2. Matériel

| Élément | Détail | Rôle actuel |
|---|---|---|
| Raspberry Pi 4 Model B | 8 Go de RAM | Machine du NAS |
| microSD | — | OS **et** données (stockage primaire, **phase de test**) |
| SSD Kingston 250 Go (SATA) | nécessite un adaptateur USB-SATA (à acheter) | Backup (prévu, pas encore en place) |
| NVMe 1 To | format M.2 / PCIe | Mis de côté pour un autre projet |
| Routeur Asus RT-AX86U Pro | non branché | Réservé à un projet futur (VPN, etc.) |

> Réseau actuel : box Free, connexion **Ethernet** du Pi.

---

## 3. Modèle d'accès — résumé

| Qui | Outil | Accès |
|---|---|---|
| `pinas` (admin) | SSH (clé) + sudo | Tout : système, dépôts git, création/suppression |
| Agents | git via SSH (groupe `agents`) | Travail dans les dépôts, pas de gestion |
| `oce` (Océane) | SMB | Uniquement son dossier `/srv/partages/oceane` |

Les deux mondes (git technique / partage familial) sont **cloisonnés** : comptes
distincts, dossiers distincts, mécanismes distincts.

---

## 4. Points de vigilance

- **Sauvegarde** : tant que le backup n'est pas en place, toutes les données
  vivent sur la **seule microSD**. Les dépôts git sont protégés s'ils sont clonés
  ailleurs (PC), mais **les fichiers d'Océane ne le sont pas** — priorité au backup.
- **microSD en 24/7** : usure possible à terme ; le passage à un SSD est prévu.
- **VPN du PC** : doit être **désactivé** pour administrer le NAS en local.

> Les tâches en attente (backup, migration SSD, VPN…) sont suivies dans
> [../backlog.md](../backlog.md).

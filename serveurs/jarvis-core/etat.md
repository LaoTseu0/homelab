# jarvis-core — état courant

> Photographie de la tour d'inférence `jarvis-core`.
> L'architecture cible est dans
> [../../architecture/inference.md](../../architecture/inference.md) ;
> les pistes non tranchées dans
> [../../exploration/inference-locale.md](../../exploration/inference-locale.md).
> Dernière mise à jour : 18 juillet 2026
> Statut : **machine raccordée, rien n'y tourne** — décisions en cours

---

## 1. État

| Élément | Valeur |
|---|---|
| Matériel | RTX 4090 24 Go, 64 Go RAM |
| Réseau | Ethernet, 192.168.1.187 (réservation DHCP à faire — backlog) |
| Socle logiciel | aucun socle serveur installé — OS cible à trancher ([inference.md §6](../../architecture/inference.md)) |
| Services Jarvis | **aucun** |

## 2. Prochaines étapes

Dans l'ordre (suivi détaillé dans [../../backlog.md](../../backlog.md),
section jarvis-core) :

1. Trancher modèle résident, serveur d'inférence, port/API et politique
   d'alimentation — les questions ouvertes de
   [inference.md §6](../../architecture/inference.md).
2. Vérifier les prérequis matériels (profil EXPO, alimentation, slots PCIe).
3. Installer le socle et le documenter dans `installation.md` (à créer ici,
   sur le modèle de
   [../jarvis-central/installation.md](../jarvis-central/installation.md)).
4. Tenir ce fichier à jour au premier service déployé.

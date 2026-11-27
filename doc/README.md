# Documentation du homelab

| Je cherche… | J’ouvre |
|---|---|
| Les équipements et leurs branchements | [Topologie physique](architecture/topologie-physique.md) |
| Les sous-réseaux et les échanges entre services | [Topologie logique](architecture/topologie-logique.md) |
| Les adresses, les ports et les accès Samba | [Réseau](architecture/reseau.md) |
| Le matériel, les systèmes et les relevés à compléter | [Machines](architecture/machines.md) |
| Les dossiers de données et le montage du NVMe | [Volumes](architecture/volumes.md) |
| Les commandes pour préparer le poste et déployer | [Déployer](exploitation/deployer.md) |
| La livraison d’une nouvelle version d’image | [Publier une image](exploitation/publier-une-image.md) |
| La reprise après la panne du NAS | [Remettre le NAS en service](exploitation/remettre-le-nas-en-service.md) |
| Ce qui donne root et la reprise d’un mot de passe perdu | [Sécurité des accès](exploitation/securite.md) |
| Les raisons des choix techniques | [Décisions](decisions/) |
| Les pistes d’évolution | [Messagerie](projets/messagerie.md) · [Pipeline CI/CD](projets/pipeline-ci-cd.md) · [Machines virtuelles](projets/virtualisation.md) |

## Organisation

- `architecture/` décrit comment l’infrastructure est construite.
- `exploitation/` rassemble les procédures à suivre.
- `decisions/` explique pourquoi un choix a été fait, avec ses compromis.
- `projets/` décrit les pistes envisagées, leur intérêt, leurs prérequis et les écarts avec les besoins en entreprise, avant toute mise en œuvre.
- `prive/` contient des notes personnelles locales. Ce dossier est ignoré par Git.

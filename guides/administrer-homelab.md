# Administrer et reconstruire le homelab

> Rôle : procédure opérateur pour le socle Ansible commun.
> Mise à jour : 6 novembre 2026.
> Statut : procédure préparée ; première exécution sur le Pi 5 à valider.

## 1. Préparer le contrôleur Linux

Le PC actuel fonctionne sous Windows et WSL n'est pas installé. Ansible doit
s'exécuter dans Linux. Installer Ubuntu sous WSL constitue le chemin proposé ;
ce changement peut nécessiter un redémarrage du PC.

Dans un PowerShell administrateur :

```powershell
wsl --install -d Ubuntu
```

Terminer l'installation Ubuntu, puis y installer la distribution Linux officielle
de mise. Le mise Windows n'installe pas automatiquement les outils dans WSL.
Ne pas remplacer mise par un Python embarqué ou un exécutable Windows.

Dans WSL, utiliser de préférence un clone du dépôt dans le système de fichiers
Linux, en préservant d'abord les modifications locales Windows. Une copie complète
du dossier est possible pour amorcer cette migration ; ne pas perdre les fichiers
non suivis. Ne jamais recréer un historique Git pour copier le projet.

Depuis `infra/` dans cette copie Linux :

```bash
mise trust
mise install
mise current
mise which python
mise exec -- python -m venv .venv
mise exec -- .venv/bin/python -m pip install -r requirements-controller.txt
mise exec -- .venv/bin/ansible-galaxy collection install -r requirements.yml -p .collections
mise exec -- .venv/bin/python validate.py
```

La version mineure Ansible est bornée ; les dépendances du contrôleur devront être
figées dans un verrou après la première validation Linux. La collection Docker est
épinglée. Le Python utilisé par les modules sur les serveurs reste celui de l'OS.

Copier les clés SSH requises dans le dossier privé Linux, avec droits 0700 pour
le dossier et 0600 pour les clés privées. Ne jamais les mettre dans ce dépôt.
Vérifier l'empreinte du nouveau NAS avant d'accepter sa nouvelle clé hôte.

## 2. Renseigner l'inventaire et auditer

```bash
cp inventory.example.yml inventory.local.yml
```

Renseigner l'IP réelle du Pi 5 et les chemins de clés Linux. Garder les serveurs
Jarvis désactivés pour le premier déploiement. Leur audit reste possible, car il
ne dépend pas de `managed_enabled`.

```bash
mise exec -- .venv/bin/ansible-inventory --graph
mise exec -- .venv/bin/ansible-playbook audit.yml --limit nas
mise exec -- .venv/bin/ansible-playbook site.yml --syntax-check
```

Si l'accès SSH échoue, corriger l'adresse, l'utilisateur ou la clé avant toute
restauration. Ne pas désactiver la vérification des clés hôtes.

## 3. Restaurer le NAS avant de remettre le miroir en service

Archive identifiée sur le PC lors de la préparation :
`C:\Users\antho\Sauvegardes\nas-rpi4-20261106-203458\nas-rpi4-backup.tar.gz`.
Sa présence et son inventaire ont été constatés ; sa restauration n'a pas été faite.

Contrôle sans extraction depuis le contrôleur Linux, avec le chemin réel de l'archive :

```bash
mise exec -- python inspect-backup.py /chemin/vers/nas-rpi4-backup.tar.gz
```

La lecture complète gzip et l'inventaire ont passé ce contrôle le 6 novembre 2026.
Les dépôts trouvés sont `framework.git`, `homelab.git`, `inference-au-harnais.git`
et `memoire-agent.git`. Les trois premiers contiennent un hook de miroir.

1. Vérifier l'archive et son empreinte, et conserver une copie intacte hors du NAS.
2. Confirmer si les données doivent vivre sur NVMe avant de les recopier.
3. Extraire dans un répertoire temporaire privé, jamais directement à la racine.
4. Examiner les dépôts Git avec leurs configurations, hooks, branches et tags.
5. Désactiver temporairement les hooks de miroir dans la copie restaurée.
6. Recréer les comptes nécessaires et faire correspondre les propriétaires : les
   identifiants numériques de l'ancien OS peuvent désigner d'autres comptes.
7. Restaurer les données Git et les fichiers familiaux aux chemins retenus.
8. Récupérer sélectivement les clés nécessaires et leurs permissions. Ne pas
   restaurer globalement l'ancien `/etc`, `/etc/passwd` ou les clés hôtes SSH.
9. Vérifier les dépôts et tester un clone depuis le PC avant d'autoriser les pushes.
10. Comparer les références avec GitHub avant de réinstaller le miroir. Le hook
    historique force les pushes : son activation prématurée peut écraser GitHub.

Pour chaque dépôt restauré, contrôler notamment l'intégrité des objets avec
`git fsck --full` et lister les références avec `git show-ref`. Pour chaque partage,
tester lecture et écriture avec le compte attendu et refus avec un autre compte.

Le rôle NAS ne restaure pas automatiquement les données et n'active aucun miroir.
Sa liste `git_repositories` crée uniquement des dépôts neufs explicitement demandés.
Laisser cette liste vide pour les dépôts qui doivent être restaurés.

Exemple de partage à ajouter à l'hôte NAS après restauration et contrôle des UID :

```yaml
samba_users:
  - oce
samba_shares:
  - name: Oceane
    path: /srv/partages/oceane
    user: oce
```

Le compte Linux est géré par Ansible ; initialiser le mot de passe Samba avec
`sudo smbpasswd -a oce` sur le NAS, ou restaurer sa base après validation de la
correspondance des comptes. Ne pas versionner de mot de passe.

## 4. Appliquer progressivement

```bash
mise exec -- .venv/bin/ansible-playbook site.yml --limit nas --check --diff --ask-become-pass
mise exec -- .venv/bin/ansible-playbook site.yml --limit nas --ask-become-pass
mise exec -- .venv/bin/ansible-playbook audit.yml --limit nas
```

La prévisualisation sur une machine vierge n'est pas une simulation complète : les
paquets absents ne sont pas réellement installés, et les étapes suivantes peuvent
donc manquer de leurs prérequis. Les changements de secrets sont masqués.

Le rôle Docker utilise le dépôt officiel et n'effectue pas de mise à niveau
générale de l'OS. Il refuse de remplacer implicitement `docker.io` ou Podman.
Il ne donne pas automatiquement l'accès au socket Docker aux utilisateurs.

## 5. Reprendre Jarvis sans perdre les données

Avant d'activer `managed_enabled` et `jarvis_migration_ready` pour lab-studio :

- Auditer les volumes et conteneurs réellement présents, relever les versions.
- Sauvegarder Home Assistant et vérifier la restauration possible.
- Vérifier le driver et le runtime NVIDIA, installés hors de ce premier socle.
- Préparer `infra/secrets/lab-studio/grafana.env` et
  `infra/secrets/lab-studio/jarvis-exporter.env` à partir des secrets existants.
- Renseigner l'image versionnée de l'exporteur ; à défaut, autoriser explicitement
  `jarvis_exporter_build: true` pour reprendre le comportement actuel.
- Activer `satellite_enabled` uniquement si son logiciel et son périphérique audio
  sont déjà installés. Son chemin actuel suppose le compte `jarvis`.

Le rôle réutilise les Compose de `deploiement/lab-studio/`. Il conserve le nom
de projet `jarvis`, le volume externe `ollama` et les chemins de données existants.
Il ne supprime pas les conteneurs orphelins ni les volumes.

```bash
mise exec -- .venv/bin/ansible-playbook audit.yml --limit lab-studio
mise exec -- .venv/bin/ansible-playbook site.yml --limit lab-studio --ask-become-pass
```

Ne plus utiliser `installer.sh` sur une machine reprise par Ansible. Il reste une
procédure historique tant que la migration n'est pas validée. Le rôle Jarvis
n'est pas encore une reconstruction complète du driver GPU et du satellite.

## 6. Vérifier après une intervention

- NAS : nouvel accès SSH, clone Git, intégrité des dépôts et accès SMB autorisés.
- Jarvis : état Compose, santé des services, conversation texte puis boucle vocale.
- Supervision : cibles Prometheus disponibles, dashboards et collecte Home Assistant.
- Persistance : données présentes après un redémarrage planifié.
- Rejouabilité : deuxième application sans changements inattendus.
- Mettre à jour les fichiers `serveurs/<machine>/etat.md` avec les résultats réels.

L'audit préparé inventorie les machines ; il ne remplace pas ces essais fonctionnels.
Un `--check` réussi ne garantit pas une restauration ni un service en bonne santé.

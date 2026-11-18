# Préparer le NVMe et le monter sur `/srv`

> Tutoriel pour le premier effacement du Crucial P310 qui contenait Windows. Mis à jour le 9 novembre 2026.
> Les commandes s’exécutent sur le Pi 5 en SSH. L’étape d’effacement détruit le contenu du disque choisi. Lors d’un remplacement du Pi, reprendre directement le montage du NVMe existant par UUID.

## 1. Identifier le disque

Vérifier que la sauvegarde NAS est disponible sur le PC. Sur le Pi, relever le disque système et le modèle, le numéro de série et les montages du Crucial.

```bash
findmnt -no SOURCE /
lsblk -o NAME,PATH,SIZE,MODEL,SERIAL,FSTYPE,MOUNTPOINTS
ls -l /dev/disk/by-id/nvme-*
```

Continuer si le système tourne sur la microSD, que le Crucial est bien le disque à vider et que `/srv` est absent ou vide. Si `/srv` contient déjà des données, les sauvegarder avant de monter quoi que ce soit dessus.

```bash
sudo ls -la /srv
findmnt --mountpoint /srv
swapon --show
```

Dans la même session, remplacer la valeur d’exemple par le lien exact du disque entier, sans suffixe de partition. Vérifier que le lien mène au Crucial et que la ligne de type `disk` correspond au numéro de série attendu. Démonter une à une les éventuelles partitions du Crucial avec `sudo umount -- /point/de/montage`, puis relancer `lsblk` pour vérifier que leurs points de montage sont vides. Si une partition du Crucial est utilisée comme swap ou par un service, résoudre cet usage avant de continuer.

```bash
disk='/dev/disk/by-id/nvme-REMPLACER_PAR_LE_LIEN_DU_CRUCIAL'
readlink -e -- "$disk"
lsblk -o NAME,SIZE,TYPE,MODEL,SERIAL,MOUNTPOINTS -- "$disk"
```

## 2. Effacer et créer une partition ext4

**À partir d’ici, les commandes sont destructives.** La commande `blkdiscard` demande au NVMe d’invalider les blocs pour le réemploi du disque. Le réemploi décrit ici correspond à un effacement logique. [Manuel `blkdiscard`](https://www.man7.org/linux/man-pages/man8/blkdiscard.8.html)

```bash
sudo blkdiscard -- "$disk"
```

Si `blkdiscard` refuse explicitement à cause de la table de partitions existante et demande `-f`, revérifier le numéro de série et l’absence de montage ou de swap sur le Crucial. L’option `--force` désactive les contrôles de sécurité de `blkdiscard`. Dans ce cas précis, la placer avant `--`, qui marque la fin des options. Si une autre erreur apparaît, s’arrêter et examiner la cause.

```bash
sudo blkdiscard --force -- "$disk"
```

Une fois l’effacement réussi, lancer `fdisk` sur le même disque. Taper `g` pour créer une table GPT, puis `n` pour créer une partition. Accepter les valeurs par défaut pour occuper le disque. Taper `p` pour vérifier le résultat, puis `w` pour l’écrire. [Manuel `fdisk`](https://man7.org/linux/man-pages/man8/fdisk.8.html)

```bash
sudo fdisk -- "$disk"
```

Attendre que Linux voie la nouvelle partition et vérifier que le lien `-part1` pointe bien vers une partition de ce Crucial avant de la formater.

```bash
sudo udevadm settle
partition="${disk}-part1"
readlink -e -- "$partition"
lsblk -o NAME,SIZE,TYPE,FSTYPE -- "$disk"
```

```bash
sudo mkfs.ext4 -L NAS_DATA "$partition"
sudo blkid -s UUID -o value "$partition"
```

## 3. Monter et vérifier

Créer `/srv`, puis ouvrir `/etc/fstab` avec `sudoedit`. Ajouter une seule ligne pour `/srv`, en remplaçant `UUID_DE_LA_PARTITION` par l’UUID ext4 relevé. L’option `nofail` permet au Pi de démarrer et de rester joignable en SSH si le disque manque.

```bash
sudo mkdir -p /srv
sudoedit /etc/fstab
```

```fstab
UUID=UUID_DE_LA_PARTITION /srv ext4 defaults,nofail 0 2
```

```bash
sudo systemctl daemon-reload
sudo findmnt --verify
sudo mount /srv
findmnt --mountpoint /srv -o SOURCE,FSTYPE,UUID,TARGET
```

Vérifier que `/srv` est en `ext4` et que l’UUID correspond, puis répéter `findmnt` après un redémarrage. Consigner cet UUID pour Ansible. Avant de restaurer les données ou d’activer Samba et le registry, prévoir un contrôle du montage attendu dans le rôle NAS et une dépendance de montage côté services. [Montages et démarrage systemd](https://www.freedesktop.org/software/systemd/man/latest/systemd.mount.html) · [Gestion du NAS](gestion-nas.md)

#!/usr/bin/env bash
# Restauration ponctuelle des données Pi 4 ; ne formate aucun disque.
# Les hooks de miroir sont conservés, mais désactivés jusqu'au contrôle GitHub.
set -euo pipefail
umask 077

test "$(id -u)" = 0 || { echo 'Exécuter avec sudo bash.' >&2; exit 1; }
archive=/home/pinas/nas-recovery/nas-rpi4-backup.tar.gz
expected=88a55cbf47c0d5796618d96c1b884103908d177c94b45f4fc2d7c694fa611d10
work=/home/pinas/nas-recovery
stage="$work/staging"
report="$work/restore-report.txt"
test -f "$archive"
id pinas >/dev/null
test "$(id -u pinas)" = 1000 || { echo 'UID administrateur inattendu : arrêt.' >&2; exit 1; }
test ! -e /srv/git || { echo '/srv/git existe déjà : refus de remplacer des données.' >&2; exit 1; }
test ! -e /srv/partages || { echo '/srv/partages existe déjà : refus de remplacer des données.' >&2; exit 1; }
test ! -e "$stage" || { echo 'Une restauration a déjà été préparée : examiner son état avant de relancer.' >&2; exit 1; }
printf '%s  %s\n' "$expected" "$archive" | sha256sum --check
gzip -t "$archive"

install -d -m 0700 -o root -g root "$stage"
# Extraction uniquement des éléments nécessaires, dans un dossier privé.
tar --extract --gzip --file "$archive" --directory "$stage" --no-same-owner \
    srv/git srv/partages etc/samba/smb.conf var/lib/samba \
    home/pinas/.ssh home/jarvisc/.ssh

echo 'Installation des services Git, SSH et Samba (sans mise à niveau générale).'
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install --no-remove --no-install-recommends -y \
    git samba smbclient rsync acl openssh-server
systemctl stop smbd nmbd

# Conserver les configurations fraîches avant toute reprise sélective.
install -d -m 0700 "$work/before-restore"
cp -a /etc/samba/smb.conf "$work/before-restore/smb.conf"
cp -a /var/lib/samba "$work/before-restore/samba"
cp -a /home/pinas/.ssh "$work/before-restore/pinas-ssh"

ensure_group() {
    local name="$1" wanted_gid="$2"
    if getent group "$name" >/dev/null; then
        test "$(getent group "$name" | cut -d: -f3)" = "$wanted_gid" || {
            echo "GID inattendu pour $name : arrêt avant restauration." >&2; exit 1;
        }
        return
    fi
    if getent group "$wanted_gid" >/dev/null; then
        echo "GID $wanted_gid déjà occupé : arrêt avant restauration." >&2; exit 1
    fi
    groupadd --gid "$wanted_gid" "$name"
}

ensure_user() {
    local name="$1" wanted_uid="$2" shell="$3"
    if id "$name" >/dev/null 2>&1; then
        echo "Compte $name déjà présent : examiner avant modification." >&2
        exit 1
    fi
    if getent passwd "$wanted_uid" >/dev/null; then
        echo "UID $wanted_uid déjà occupé : arrêt avant restauration." >&2; exit 1
    fi
    useradd --create-home --uid "$wanted_uid" --gid "$name" --shell "$shell" "$name"
}

ensure_group agents 1002
ensure_group oce 1003
ensure_group jarvisc 1004
ensure_group antho 1005
ensure_user oce 1001 /usr/sbin/nologin
ensure_user jarvisc 1004 /bin/bash
ensure_user antho 1005 /usr/sbin/nologin
usermod -a -G agents pinas
usermod -a -G agents jarvisc

# Le compte et le mot de passe Linux actuels de pinas sont conservés.
# Les comptes techniques restent verrouillés pour l'accès par mot de passe Linux.
cp -a "$stage/srv/git" /srv/git
cp -a "$stage/srv/partages" /srv/partages
chown -R pinas:agents /srv/git
chmod 2775 /srv/git
chown root:root /srv/partages
chmod 0755 /srv/partages
chown -R oce:oce /srv/partages/oceane
chmod 0700 /srv/partages/oceane
chown -R antho:antho /srv/partages/antho
chmod 0700 /srv/partages/antho

for repo in /srv/git/*.git; do
    test -d "$repo"
    if test -f "$repo/hooks/post-receive"; then
        mv "$repo/hooks/post-receive" "$repo/hooks/post-receive.restore-disabled"
    fi
    # Accès multi-compte exact, sans toucher aux identités auteur/committer.
    if ! git config --system --get-all safe.directory | grep -Fxq "$repo"; then
        git config --system --add safe.directory "$repo"
    fi
    runuser -u pinas -- git --git-dir="$repo" fsck --full
done

# Préserver la clé publique du nouvel accès administrateur et ajouter les anciennes.
cat /home/pinas/.ssh/authorized_keys "$stage/home/pinas/.ssh/authorized_keys" \
    | awk 'NF && !seen[$0]++' > "$work/authorized_keys.merged"
install -d -m 0700 -o pinas -g pinas /home/pinas/.ssh
install -m 0600 -o pinas -g pinas "$work/authorized_keys.merged" /home/pinas/.ssh/authorized_keys
for name in config known_hosts id_ed25519_github id_ed25519_github.pub; do
    if test -f "$stage/home/pinas/.ssh/$name"; then
        install -m 0600 -o pinas -g pinas "$stage/home/pinas/.ssh/$name" "/home/pinas/.ssh/$name"
    fi
done
install -d -m 0700 -o jarvisc -g jarvisc /home/jarvisc/.ssh
install -m 0600 -o jarvisc -g jarvisc "$stage/home/jarvisc/.ssh/authorized_keys" \
    /home/jarvisc/.ssh/authorized_keys

# Restaurer ensemble les identités Samba et leurs mots de passe, services arrêtés.
# Ne pas reprendre les caches winbind/netlogon de l'ancien système.
install -d -m 0700 -o root -g root /var/lib/samba/private
for db in private/passdb.tdb private/secrets.tdb group_mapping.tdb account_policy.tdb share_info.tdb; do
    test -f "$stage/var/lib/samba/$db"
    install -m 0600 -o root -g root "$stage/var/lib/samba/$db" "/var/lib/samba/$db"
done
install -m 0644 -o root -g root "$stage/etc/samba/smb.conf" /etc/samba/smb.conf
testparm -s /etc/samba/smb.conf >/dev/null
pdbedit -L
systemctl enable --now smbd nmbd
systemctl is-active smbd nmbd

{
    printf 'Restauration exécutée le %s\n' "$(date --iso-8601=seconds)"
    echo 'Git :'
    for repo in /srv/git/*.git; do
        printf '\n%s\n' "$repo"
        runuser -u pinas -- git --git-dir="$repo" show-ref || {
            result=$?
            test "$result" = 1
            echo '(dépôt sans référence)'
        }
    done
    printf '\nComptes Samba :\n'
    pdbedit -L
    printf '\nPermissions :\n'
    stat -c '%A %U:%G %n' /srv/git /srv/git/*.git /srv/partages/*
    printf '\nMiroirs : hooks post-receive.restore-disabled, aucune synchronisation effectuée.\n'
} > "$report"
chmod 0600 "$report"
echo "Restauration terminée. Rapport : $report"
echo 'GitHub reste désactivé jusqu’à comparaison des références.'
echo 'Les fichiers, mots de passe Samba et accès Git SSH doivent maintenant être vérifiés.'

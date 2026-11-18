#!/usr/bin/env bash
# Restauration ponctuelle de l'archive Pi 4 sur le NVMe déjà monté du Pi 5.
set -euo pipefail
umask 077

die() { printf '%s\n' "$*" >&2; exit 1; }

archive=/home/pinas/nas-recovery/nas-rpi4-backup.tar.gz
expected_hash=88a55cbf47c0d5796618d96c1b884103908d177c94b45f4fc2d7c694fa611d10
expected_uuid=97498878-33ac-4e4b-bc8f-c6094172f15c
repos=(framework.git homelab.git inference-au-harnais.git memoire-agent.git)
samba_db=(private/passdb.tdb private/secrets.tdb group_mapping.tdb account_policy.tdb share_info.tdb)

test "$EUID" -eq 0 || die 'Lancer avec sudo.'
test "$(findmnt -n -o UUID --mountpoint /srv)" = "$expected_uuid" || die 'NVMe attendu absent de /srv.'
test "$(id -u pinas)" = 1000 || die 'UID inattendu pour pinas.'
for path in /srv/git /srv/partages /srv/samba /etc/systemd/system/smbd.service.d/nas-storage.conf; do
    test ! -e "$path" && test ! -L "$path" || die "Chemin déjà présent : $path. Examiner avant de relancer."
done
resume=false
case $# in
    0) stage=$(mktemp -d /srv/.restore-nas.XXXXXXXX) ;;
    2)
        test "$1" = --resume || die 'Usage : restore-nas-pi5.sh [--resume /srv/.restore-nas.XXXXXXXX]'
        stage=$2
        [[ "$stage" =~ ^/srv/\.restore-nas\.[[:alnum:]]{8}$ ]] && test -d "$stage" && test ! -L "$stage" &&
            test "$(stat -c '%u:%g:%a' "$stage")" = 0:0:700 || die 'Dossier de préparation inattendu.'
        resume=true
        ;;
    *) die 'Usage : restore-nas-pi5.sh [--resume /srv/.restore-nas.XXXXXXXX]' ;;
esac
trap 'printf "Échec. Vérifier les chemins en place et le dossier de préparation %s avant de relancer.\n" "$stage" >&2' ERR
if "$resume"; then
    printf 'Reprise depuis %s\n' "$stage"
    for program in git testparm pdbedit; do
        command -v "$program" >/dev/null || die "Outil manquant pour la reprise : $program."
    done
else
    printf '%s  %s\n' "$expected_hash" "$archive" | sha256sum --check
    gzip -t "$archive"
    tar --extract --gzip --file "$archive" --directory "$stage" --no-same-owner --acls --xattrs \
        srv/git srv/partages "${samba_db[@]/#/var/lib/samba/}"
    install -d -m 0700 "$stage/samba/private"
    for db in "${samba_db[@]}"; do
        install -m 0600 "$stage/var/lib/samba/$db" "$stage/samba/$db"
    done
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install --no-remove --no-install-recommends -y git samba smbclient
fi
for repo in "${repos[@]}"; do
    test -f "$stage/srv/git/$repo/HEAD"
done
for share in oceane antho; do
    test -d "$stage/srv/partages/$share"
done
for db in "${samba_db[@]}"; do
    test -s "$stage/samba/$db"
done
systemctl stop smbd nmbd

ensure_group() {
    local name=$1 gid=$2 entry
    entry=$(getent group "$gid" || true)
    if test "${entry%%:*}" = "$name"; then return; fi
    "$resume" && die "Groupe $name (GID $gid) introuvable pour la reprise."
    test -z "$entry" && ! getent group "$name" >/dev/null || die "Conflit pour le groupe $name (GID $gid)."
    groupadd --gid "$gid" "$name"
}

ensure_share_user() {
    local name=$1 uid=$2
    if id "$name" >/dev/null 2>&1; then
        test "$(id -u "$name")" = "$uid" && test "$(id -gn "$name")" = "$name" &&
            test "$(getent passwd "$name" | cut -d: -f7)" = /usr/sbin/nologin || die "Compte $name inattendu."
        return
    fi
    "$resume" && die "Compte $name introuvable pour la reprise."
    ! getent passwd "$uid" >/dev/null || die "UID $uid déjà utilisé."
    useradd --no-create-home --uid "$uid" --gid "$name" --shell /usr/sbin/nologin "$name"
}

ensure_group agents 1002
ensure_group oce 1003
ensure_group antho 1005
ensure_share_user oce 1001
ensure_share_user antho 1005
if ! id -nG pinas | tr ' ' '\n' | grep -Fxq agents; then
    "$resume" && die 'Le compte pinas doit déjà appartenir au groupe agents pour cette reprise.'
    usermod -a -G agents pinas
fi

chown -R pinas:agents "$stage/srv/git"
chmod 2750 "$stage/srv/git"
for repo in "${repos[@]}"; do
    path="$stage/srv/git/$repo"
    if test -e "$path/hooks/post-receive"; then
        mv -- "$path/hooks/post-receive" "$path/hooks/post-receive.restore-disabled"
    fi
    git config --file "$path/config" --replace-all core.hooksPath /dev/null
    git -c safe.directory="$path" --git-dir="$path" fsck --full
done
chown root:root "$stage/srv/partages"
chmod 0755 "$stage/srv/partages"
chown -R oce:oce "$stage/srv/partages/oceane"
chown -R antho:antho "$stage/srv/partages/antho"
chmod 0700 "$stage/srv/partages/"{oceane,antho}

cat > "$stage/smb.conf" <<'EOF'
[global]
    server role = standalone server
    security = user
    map to guest = Never
    server min protocol = SMB2
    load printers = no
    disable spoolss = yes
    passdb backend = tdbsam
    private dir = /srv/samba/private
    state directory = /srv/samba

[Oceane]
    path = /srv/partages/oceane
    valid users = oce
    guest ok = no
    read only = no
    create mask = 0600
    directory mask = 0700

[antho]
    path = /srv/partages/antho
    valid users = antho
    guest ok = no
    read only = no
    create mask = 0600
    directory mask = 0700
EOF
samba_options=(--option="state directory=$stage/samba" --option="private dir=$stage/samba/private")
testparm -s "${samba_options[@]}" "$stage/smb.conf" >/dev/null
accounts=$(pdbedit --configfile="$stage/smb.conf" "${samba_options[@]}" -L)
for account in oce antho; do
    printf '%s\n' "$accounts" | cut -d: -f1 | grep -Fxq "$account" || die "Compte Samba introuvable : $account."
done
cp -a /etc/samba/smb.conf "$stage/smb.conf.before-restore"

printf '%s\n' 'Contrôles réussis. Mise en service des données sur /srv.'
test "$(findmnt -n -o UUID --mountpoint /srv)" = "$expected_uuid" || die 'NVMe absent avant la mise en place.'
mv -T --no-clobber -- "$stage/srv/git" /srv/git && test ! -e "$stage/srv/git" || die '/srv/git existe déjà.'
mv -T --no-clobber -- "$stage/srv/partages" /srv/partages && test ! -e "$stage/srv/partages" || die '/srv/partages existe déjà.'
mv -T --no-clobber -- "$stage/samba" /srv/samba && test ! -e "$stage/samba" || die '/srv/samba existe déjà.'

testparm -s "$stage/smb.conf" >/dev/null
install -m 0644 "$stage/smb.conf" /etc/samba/smb.conf
install -d -m 0755 /etc/systemd/system/smbd.service.d
cat > /etc/systemd/system/smbd.service.d/nas-storage.conf <<EOF
[Unit]
RequiresMountsFor=/srv
AssertPathIsMountPoint=/srv

[Service]
ExecStartPre=/usr/bin/findmnt --noheadings --mountpoint /srv --source UUID=$expected_uuid
EOF
chmod 0644 /etc/systemd/system/smbd.service.d/nas-storage.conf
systemctl daemon-reload
systemctl enable --now smbd
systemctl is-active smbd

for repo in "${repos[@]}"; do
    runuser -u pinas -- git ls-remote "/srv/git/$repo" >/dev/null
    printf 'Git OK : %s\n' "$repo"
done
printf '%s\n' 'Comptes Samba présents : oce et antho. Vérifier les accès depuis le PC.'
printf 'Restauration terminée. Ancienne configuration Samba et extraction privée : %s\n' "$stage"

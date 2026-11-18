#!/usr/bin/env bash
# Essai temporaire du noyau officiel 6.12, sans effacement des données.
# À exécuter sur le NAS en root ; ne redémarre pas automatiquement.
set -euo pipefail

test "$(id -u)" = 0 || { echo 'Utiliser sudo bash pour ce script.' >&2; exit 1; }
work=/home/pinas/nas-pcie-diagnostic
boot=/boot/firmware
version=6.12.75+rpt-rpi-2712
package="$work/linux-image-${version}_1%3a6.12.75-1+rpt1_arm64.deb"
expected=4980f0626018b70499ab43fae5969e7c8662ac6938de987fc49755c34c2104d4

test "$(uname -r)" = '6.18.50+rpt-rpi-2712' || {
    echo 'Version en cours différente du diagnostic prévu : arrêt.' >&2; exit 1;
}
test -f "$package"
test -f "$boot/overlays/pcie-fix.dtbo"
mountpoint -q "$boot"
test ! -e "$work/config.before-kernel612" || {
    echo 'Une sauvegarde de cet essai existe déjà ; ne pas la remplacer.' >&2; exit 1;
}
printf '%s  %s\n' "$expected" "$package" | sha256sum --check

# L'archive permet aussi de récupérer les fichiers de démarrage depuis un autre PC.
cp -a "$boot/config.txt" "$work/config.before-kernel612"
tar -cpf "$work/boot-before-kernel612.tar" -C "$boot" .
chmod 600 "$work/config.before-kernel612" "$work/boot-before-kernel612.tar"

# Le paquet 6.18 reste installé. Refuser toute suppression de paquet.
apt-get install --no-remove --no-install-recommends -y "$package"
test -s "/boot/vmlinuz-$version"
test -s "/boot/initrd.img-$version"
test -d "/lib/modules/$version"

install -d -m 0755 "$boot/diag612/overlays"
cp "/boot/vmlinuz-$version" "$boot/diag612/kernel_2712.img"
cp "/boot/initrd.img-$version" "$boot/diag612/initramfs_2712"
cp "$boot/cmdline.txt" "$boot/diag612/cmdline.txt"
cp /usr/lib/linux-image-"$version"/broadcom/bcm27*.dtb "$boot/diag612/"
cp /usr/lib/linux-image-"$version"/overlays/*.dtbo "$boot/diag612/overlays/"
cp /usr/lib/linux-image-"$version"/overlays/README "$boot/diag612/overlays/README"
cp "$boot/overlays/pcie-fix.dtbo" "$boot/diag612/overlays/pcie-fix.dtbo"

# Sélectionner ensemble noyau, DTB, overlays et initramfs de cet essai.
# Restaurer config.before-kernel612 annule cette sélection.
printf '\n[all]\n# Diagnostic temporaire PCIe : noyau officiel 6.12\nos_prefix=diag612/\n' >> "$boot/config.txt"
sync
echo 'Essai préparé. Le système tourne encore sur le noyau 6.18.'
echo 'Garder le HAT connecté et le SSD retiré pour comparer le même matériel.'
echo 'Redémarrage : sudo reboot'
echo 'Après reconnexion : uname -r ; lspci -nn'
echo 'Retour au noyau initial :'
echo 'sudo cp /home/pinas/nas-pcie-diagnostic/config.before-kernel612 /boot/firmware/config.txt'
echo 'sudo reboot'

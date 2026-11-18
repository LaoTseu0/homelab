#!/usr/bin/env bash
# Active uniquement la trace de négociation du pilote PCIe pour le prochain boot.
set -euo pipefail
test "$(id -u)" = 0 || { echo 'Exécuter avec sudo bash.' >&2; exit 1; }
cmdline=/boot/firmware/cmdline.txt
backup=/boot/firmware/cmdline.txt.before-pcie-trace
test -f /sys/module/pcie_brcmstb/parameters/trace_ltssm
test "$(awk 'END {print NR}' "$cmdline")" = 1 || {
    echo 'La ligne de démarrage doit contenir une seule ligne : arrêt.' >&2; exit 1;
}
if grep -q 'pcie_brcmstb.trace_ltssm=' "$cmdline"; then
    echo 'Un réglage de trace existe déjà : aucune modification.'
    exit 0
fi
if test ! -e "$backup"; then
    cp -a "$cmdline" "$backup"
fi
sed -i -e 's/[[:space:]]*$//' -e 's/$/ pcie_brcmstb.trace_ltssm=1/' "$cmdline"
sync
echo 'Trace activée pour le prochain démarrage ; aucun autre réglage changé.'
echo "Sauvegarde : $backup"
echo 'Redémarrer avec sudo reboot, puis laisser le Pi allumé pour la collecte SSH.'

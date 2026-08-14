#!/bin/sh
# Installe le hook de miroir GitHub sur les depots bare du NAS.
#
# Cible tous les depots de /srv/git/*.git qui declarent un remote "github" ;
# les autres sont ignores. Idempotent : relancable sans effet de bord, un
# depot deja a jour n'est pas touche.
#
# A executer sur le NAS, en tant que pinas :
#     cd ~/homelab/deploiement/nas && ./installer-miroir.sh

set -eu

src="$(dirname "$0")/post-receive"

if [ ! -f "$src" ]; then
    echo "Hook source introuvable : $src" >&2
    exit 1
fi

if ! sh -n "$src"; then
    echo "Le hook source contient une erreur de syntaxe, rien n'a ete installe." >&2
    exit 1
fi

for repo in /srv/git/*.git; do
    nom="$(basename "$repo")"
    url="$(git --git-dir="$repo" config remote.github.url || echo '')"

    if [ -z "$url" ]; then
        printf '%-28s ignore (aucun remote github)\n' "$nom"
        continue
    fi

    hook="$repo/hooks/post-receive"

    if [ -f "$hook" ] && cmp -s "$src" "$hook"; then
        printf '%-28s deja a jour\n' "$nom"
        continue
    fi

    if [ -f "$hook" ]; then
        cp -p "$hook" "$hook.bak"
    fi

    cp "$src" "$hook"
    chmod 775 "$hook"
    chgrp agents "$hook" 2>/dev/null || true

    printf '%-28s installe -> %s\n' "$nom" "$url"
done

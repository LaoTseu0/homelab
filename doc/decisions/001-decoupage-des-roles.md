# 001 — Découper les rôles Ansible par fonction

**Statut :** accepté, déploiement sur les machines à réaliser.
**Date :** novembre 2026.

## Contexte

Les rôles `nas` et `lab-studio` portaient le nom d’une machine et mélangeaient plusieurs responsabilités : montage du disque, Samba, Git, GPU, services applicatifs. Le playbook de la tour contenait aussi une grande partie de la logique, et Docker était décrit par deux variantes. Réutiliser une de ces fonctions sur une nouvelle machine demandait de copier du code.

## Décision

- Chaque rôle représente **une capacité** : `samba`, `docker`, `nvidia_gpu`, `ollama`…
- Chaque rôle déclare son interface dans `defaults/main.yml`.
- Les playbooks `configurer-*.yml` servent de **profils** : ils listent seulement les rôles d’une machine.
- Ollama et Home Assistant deviennent deux projets Compose. Ollama a son propre cycle de vie, tandis que Whisper, Piper et openWakeWord n’existent que pour la chaîne vocale de Home Assistant.

## Alternatives écartées

- **Rôles profils dédiés :** une couche d’indirection sans bénéfice pour quelques machines, les playbooks remplissent déjà cette fonction.
- **Groupes d’inventaire immédiats :** aucune variable n’est encore partagée par un sous-ensemble de machines. Ils seront ajoutés avec une seconde machine GPU.
- **`ansible.cfg` dans le dépôt :** Ansible l’ignore dans un dossier accessible en écriture à tous, ce qui est le cas de `/mnt/c` sous WSL avec la configuration actuelle.

## Conséquences

- Une nouvelle machine se compose à partir de rôles existants, et une application peut être livrée seule avec un tag.
- Le changement de projet Compose impose une migration ponctuelle et une courte coupure des services de la tour.
- Le nombre de rôles augmente, donc l’ordre d’application dans les profils devient important : par exemple `docker` avant `nvidia_gpu`.

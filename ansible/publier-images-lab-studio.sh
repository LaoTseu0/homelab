#!/usr/bin/env bash
set -euo pipefail

studio_ssh='studio@192.168.50.252'
studio_key="$HOME/.ssh/id_ed25519_jarvis_central"
nas_ssh='pinas'
publication='192.168.50.198:5000'
lecture='192.168.50.198:5001'
services=(ollama homeassistant whisper piper openwakeword)

# Lire l’image du conteneur, même si le tag amont désigne une autre version.
studio=(ssh -T -i "$studio_key" "$studio_ssh")
inspection=$("${studio[@]}" \
  "docker container inspect --format '{{.Name}} {{.Image}} {{.State.Running}}' ${services[*]}")

exports=()
tags=()
while read -r name image running; do
  service=${name#/}
  if [[ ! "$service" =~ ^(ollama|homeassistant|whisper|piper|openwakeword)$ ||
        ! "$image" =~ ^sha256:[0-9a-f]{64}$ || "$running" != true ]]; then
    printf 'Conteneur à vérifier sur lab-studio : %s\n' "$name" >&2
    exit 1
  fi

  tag="$publication/studio/$service:adoption-amd64-${image:7:12}"
  exports+=("$image" "$tag")
  tags+=("$tag")
done <<< "$inspection"

if [[ "${#tags[@]}" -ne "${#services[@]}" ]]; then
  printf 'Le relevé Docker doit contenir les cinq services à publier.\n' >&2
  exit 1
fi

# Le NAS écrit l’archive temporaire sur le NVMe.
ssh -t "$nas_ssh" \
  'mountpoint -q /srv && sudo install -d -m 0700 -o "$(id -u)" -g "$(id -g)" /srv/registry/import-images'
stage=$(ssh -T "$nas_ssh" \
  'mountpoint -q /srv && mktemp -d /srv/registry/import-images/lab-studio.XXXXXXXX')
if [[ ! "$stage" =~ ^/srv/registry/import-images/lab-studio\.[a-zA-Z0-9]+$ ]]; then
  printf 'Répertoire temporaire du NAS inattendu.\n' >&2
  exit 1
fi

printf 'Transfert des images vers %s sur le NAS. Cela peut prendre quelques minutes.\n' "$stage"
"${studio[@]}" "bash -s -- $(printf '%q ' "${exports[@]}")" <<'EXPORT_IMAGES' | \
  ssh -T "$nas_ssh" "mountpoint -q /srv && umask 077 && cat > '$stage/images.tar.gz'"
set -euo pipefail
tags=()
while (( $# > 0 )); do
  image=$1
  tag=$2
  shift 2

  platform=$(docker image inspect --format '{{.Os}}/{{.Architecture}}' "$image")
  if [[ "$platform" != linux/amd64 ]]; then
    printf 'Plateforme inattendue pour %s : %s\n' "$tag" "$platform" >&2
    exit 1
  fi

  docker image tag "$image" "$tag"
  tags+=("$tag")
done

docker image save "${tags[@]}" | gzip -1
EXPORT_IMAGES

publish_script=$(cat <<'PUBLISH_IMAGES'
set -euo pipefail
stage=$1
publication=$2
lecture=$3
shift 3

mountpoint -q /srv
sudo docker image load --input "$stage/images.tar.gz"
sudo docker login "$publication" --username publisher

# Le digest de publication est celui du manifeste, pas l’ID de configuration de l’image.
for tag in "$@"; do
  repository=${tag%:*}
  service=${repository##*/}
  sudo docker image push --platform linux/amd64 "$tag" | tee "$stage/$service.push.log"
  digest=$(awk '$2 == "digest:" {print $3}' "$stage/$service.push.log" | tail -n 1)
  if [[ ! "$digest" =~ ^sha256:[0-9a-f]{64}$ ]]; then
    printf 'Digest de publication introuvable pour %s.\n' "$service" >&2
    exit 1
  fi
  printf '  %s: "%s/%s@%s"\n' "$service" "$lecture" "${repository#*/}" "$digest" >> "$stage/images.yml"
done

rm -- "$stage/images.tar.gz"
printf '\nRéférences publiées sur le NAS\n'
cat "$stage/images.yml"
PUBLISH_IMAGES
)
ssh -t "$nas_ssh" \
  "bash -c $(printf '%q' "$publish_script") bash $(printf '%q ' "$stage" "$publication" "$lecture" "${tags[@]}")"

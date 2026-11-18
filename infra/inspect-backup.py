"""Vérifier une archive du NAS sans l'extraire ni afficher ses secrets."""

import argparse
import gzip
import hashlib
import tarfile
from pathlib import Path, PurePosixPath


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    with args.archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    # Lire jusqu'à la fin pour vérifier le CRC gzip, y compris après la fin du tar.
    with gzip.open(args.archive, "rb") as stream:
        while stream.read(1024 * 1024):
            pass
    with tarfile.open(args.archive, "r:gz") as archive:
        names = set()
        repositories = set()
        for member in archive:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("Chemin dangereux dans l'archive : extraction refusée")
            names.add(str(path))
            if len(path.parts) == 4 and path.parts[:2] == ("srv", "git") and path.name == "HEAD":
                repositories.add(path.parts[2])
        for required in ("srv/git", "home", "etc", "var/lib/samba"):
            if required not in names:
                raise ValueError(f"Répertoire attendu absent : {required}")
    print(f"SHA256 : {digest}")
    print(f"Archive gzip lisible ; {len(names)} entrées ; chemins relatifs contrôlés.")
    print("Dépôts bare trouvés : " + ", ".join(sorted(repositories)))
    for repository in sorted(repositories):
        hook = f"srv/git/{repository}/hooks/post-receive"
        print(f"Miroir {repository} : hook {'présent' if hook in names else 'absent'}")
    print("Ce contrôle ne remplace pas un essai de restauration et git fsck.")


if __name__ == "__main__":
    main()

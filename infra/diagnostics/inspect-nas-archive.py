"""Lire les métadonnées nécessaires à la restauration, sans afficher de secrets."""
import json
import tarfile
from pathlib import Path

archive_path = Path.home() / "Sauvegardes/nas-rpi4-20261106-203458/nas-rpi4-backup.tar.gz"
with tarfile.open(archive_path, "r:gz") as archive:
    members = {m.name.rstrip("/"): m for m in archive.getmembers()}

    def read(name):
        member = members.get(name)
        if not member or not member.isfile():
            return ""
        return archive.extractfile(member).read().decode("utf-8", errors="replace")

    accounts = [line.split(":") for line in read("etc/passwd").splitlines()]
    groups = [line.split(":") for line in read("etc/group").splitlines()]
    print(json.dumps({
        "old_os": read("etc/os-release"),
        "accounts": [dict(name=a[0], uid=a[2], gid=a[3], home=a[5], shell=a[6])
                     for a in accounts if int(a[2]) >= 1000 and int(a[2]) < 65534],
        "groups": [g for g in groups if g[0] in {"agents", "pinas", "oce", "antho"}],
        "samba_config": read("etc/samba/smb.conf"),
        "ssh_files": [n for n in members if n.startswith("home/pinas/.ssh/")],
        "technical_home_files": [n for n in members if n.startswith("home/jarvisc/") and not members[n].isdir()],
        "service_data": [dict(path=n, uid=m.uid, gid=m.gid, mode=oct(m.mode), size=m.size)
                         for n,m in members.items() if n.startswith("srv/") and n.count("/") <= 2],
        "samba_databases": [n for n in members if n.startswith("var/lib/samba/")],
    }, indent=2, ensure_ascii=False))

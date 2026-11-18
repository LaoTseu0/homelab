"""Contrôle statique ; ne remplace pas ansible-playbook --syntax-check."""

from pathlib import Path

import yaml
from jinja2 import Environment


class UniqueKeysLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"Clé YAML dupliquée : {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeysLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping
)


def validate_strings(value, environment):
    if isinstance(value, dict):
        for item in value.values():
            validate_strings(item, environment)
    elif isinstance(value, list):
        for item in value:
            validate_strings(item, environment)
    elif isinstance(value, str) and ("{{" in value or "{%" in value):
        environment.parse(value)


def main():
    root = Path(__file__).resolve().parent
    environment = Environment()
    files = sorted(root.rglob("*.yml"))
    count = 0
    for path in files:
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        if "secrets" in path.relative_to(root).parts:
            continue
        value = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeysLoader)
        validate_strings(value, environment)
        count += 1
    for path in root.rglob("*.j2"):
        environment.parse(path.read_text(encoding="utf-8"))
    inventory = yaml.safe_load((root / "inventory.example.yml").read_text(encoding="utf-8"))
    studio = inventory["all"]["children"]["jarvis_servers"]["hosts"]["lab-studio"]
    assert studio["ansible_user"] == "studio"
    assert studio["managed_enabled"] is False
    assert studio["jarvis_migration_ready"] is False
    print(f"OK : {count} fichiers YAML, expressions Jinja et garde-fous de l'inventaire.")
    print("Exécution Ansible et validation sur les machines encore nécessaires.")


if __name__ == "__main__":
    main()

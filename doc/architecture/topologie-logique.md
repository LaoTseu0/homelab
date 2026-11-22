# Topologie logique

## Réseaux et accès

```mermaid
flowchart TD
    internet["Internet"]

    subgraph maison["Réseau Maison"]
        bbox["Bbox · passerelle et DHCP"]
        phones["Téléphones autorisés"]
    end

    subgraph passerelle["Pi 4 · lab-rpi4-1"]
        routage["NetworkManager · NAT IPv4 et relais DNS"]
        proxy["HAProxy · relais SMB"]
    end

    subgraph lab["Réseau Homelab"]
        admin["PC admin · Windows et WSL"]
        nas["NAS · Pi 5"]
        studio["lab-studio"]
    end

    admin -->|"Accès Internet et DNS"| routage
    nas -->|"Accès Internet et DNS"| routage
    studio -->|"Accès Internet et DNS"| routage
    routage --> bbox
    bbox --> internet
    phones -->|"SMB"| proxy
    proxy -->|"SMB · après filtrage IP"| nas
    admin -->|"SSH Ansible et SMB direct"| nas
    admin -->|"SSH Ansible"| passerelle
    admin -->|"SSH Ansible et interfaces web"| studio
    studio -->|"Git sur SSH et pull du registry en TLS"| nas
```

Le Pi 4 fournit aussi le DHCP du Homelab. Pour le SMB relayé, HAProxy vérifie l’adresse source et Samba vérifie ensuite le compte et les droits du partage. Le registry du NAS dispose d’un point d’accès de publication et d’un point d’accès de lecture. Tous deux utilisent le même stockage d’images.

## Services sur lab-studio

```mermaid
flowchart LR
    ha["Home Assistant"]
    ha -->|"Wyoming · transcription"| whisper["Whisper"]
    ha -->|"Wyoming · synthèse vocale"| piper["Piper"]
    ha -->|"Wyoming · détection du mot d’activation"| wake["openWakeWord"]
    ha -->|"API d’inférence"| ollama["Ollama"]
```

Les flèches indiquent quel composant initie chaque échange. Le schéma vocal décrit la chaîne de services. Le satellite est à l’arrêt, et la chaîne complète reste à retester après son rebranchement.

Les sous-réseaux, les adresses IP et les ports sont détaillés dans [Réseau](reseau.md).

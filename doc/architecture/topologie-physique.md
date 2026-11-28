# Topologie physique

```mermaid
flowchart TD
    internet["Internet"] --- bbox["Bbox"]
    bbox ---|"Wi-Fi Maison"| maison["PC d’Océane et deux téléphones"]
    bbox ---|"Wi-Fi 5 GHz · wlan0"| pi4["Pi 4 · lab-rpi4-1"]
    pi4 ---|"Ethernet · eth0"| switch["Switch TP-Link TL-SG108PE"]
    switch ---|"Ethernet"| admin["PC admin"]
    switch ---|"Ethernet"| nas["Pi 5 · NAS"]
    switch ---|"Ethernet · enp4s0"| studio["lab-studio"]
    switch ---|"Ethernet · enp12s0"| forge["lab-forge"]
    nas ---|"Emplacement microSD"| boot["microSD système"]
    nas ---|"PCIe via HAT"| nvme["NVMe de données"]
    studio -.->|"USB · débranché"| audio["ReSpeaker XVF3800"]
```

Le Pi 4 relie la Bbox en Wi-Fi au switch en Ethernet. `lab-forge` est branché sur le switch. Son Wi-Fi est inactif.

Pour les composants et leurs références, voir [Machines](machines.md). Les adresses des interfaces se trouvent dans [Réseau](reseau.md#adressage).

# Projet : boîte mail personnelle

## Tu peux utiliser ton Raspberry Pi sans ouvrir de ports

Et c'est probablement la solution qui va t'intéresser.

Il existe un outil appelé Tailscale, qui permet de créer un réseau privé chiffré entre ton Raspberry Pi, ton ordinateur et ton téléphone.

### Réseau privé Tailscale

- Raspberry Pi 5
- Ton ordinateur
- Ton téléphone

Connexions privées chiffrées.

Pas de redirection de port manuelle nécessaire sur ta Bbox dans une configuration Tailscale classique.

[Tailscale Docs](https://tailscale.com/kb)

Tu pourrais être à l'extérieur de chez toi et te connecter à ton Raspberry Pi pour administrer Debian ou accéder à un serveur IMAP privé.

Attention : Tailscale ne permet pas à tous les serveurs Gmail ou Outlook de livrer directement des messages à ton Pi. Pour une vraie boîte mail publique, il faudrait un relais de réception externe ou exposer un serveur SMTP joignable.

## Les précautions que je prendrais sur ta Bbox

- Garder le pare-feu activé.
- Ne pas utiliser le mode DMZ pour le Raspberry Pi.
- Ne pas activer l'administration de la Bbox depuis Internet.
- Désactiver l'UPnP si tu n'en as pas besoin, pour éviter des ouvertures automatiques de ports.
- Mettre régulièrement à jour Debian et les logiciels du Pi.
- Utiliser SSH avec des clés plutôt qu'un mot de passe.
- Sauvegarder régulièrement les données du Pi.

Pour aller plus loin, tu pourrais également isoler ton Raspberry Pi sur un réseau séparé afin de limiter les conséquences d'une éventuelle compromission.

## Ce que je ferais à ta place

### Messagerie quotidienne : chez un hébergeur

Domaine + boîte IMAP chez OVHcloud, Infomaniak ou un autre prestataire. Pas de port à ouvrir sur ta Bbox.

### Raspberry Pi 5 : ton laboratoire personnel

Debian + Docker + Tailscale, puis Postfix, Dovecot, DNS, pare-feu et supervision. Tu peux apprendre à construire une messagerie sans exposer ton réseau domestique.

Cette configuration te permettrait d'apprendre énormément en réseau et cybersécurité, tout en conservant une boîte mail fiable.


# Fichier des projets à explorer.

Ce fichier rassemble les projets à explorer pour améliorer continuellement le homelab et le faire évoluer vers des pratiques professionnelles. Il permet de décrire les pistes envisagées, leur intérêt, les prérequis et les écarts entre l’infrastructure actuelle et les besoins en entreprise, avant de décider de leur mise en œuvre.

# Exploration : création de boîte mail perso.

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

# Exploration : pipeline CI/CD pour homelab

## Point de départ dans l’infrastructure actuelle

Le dépôt décrit une administration depuis le PC Windows, avec Ansible exécuté dans Ubuntu sous WSL. Ansible configure les hôtes Linux par SSH et déploie les services Docker Compose. Le NAS Pi 5 héberge des dépôts Git et un registry privé avec des accès distincts pour la publication et le téléchargement des images. La tour `lab-studio` exécute les applications et dispose d’une supervision Prometheus/Grafana.

La [procédure de publication](exploitation.md#publier-une-version-dimage) prévoit déjà de publier une image, de relever son digest, de mettre à jour les variables Ansible puis de redéployer. Le digest identifie précisément le contenu de l’image. C’est une bonne base pour automatiser les livraisons et retrouver une version précédente.

Cette section décrit une évolution possible à partir des fichiers du dépôt, sans vérification des machines en fonctionnement. Aucun pipeline CI/CD ni runner n’a été identifié dans ce dépôt. Un serveur Git conserve le code ; il faut lui ajouter un moteur CI/CD pour déclencher et suivre des tâches. Le runner est la machine ou le processus qui les exécute.

## Exemple : mettre à jour une application personnelle

Pour une application dont le code est maîtrisé, comme le composant `jarvis-exporter` présent dans le dépôt, le parcours cible pourrait être :

```text
Modification du code et push d’une branche
                    ↓
CI : vérifications du code, tests, construction de contrôle
                    ↓
Relecture puis fusion dans la branche principale
                    ↓
Construction de l’image à publier, adaptée à la cible
                    ↓
Publication dans le registry du NAS et relevé du digest
                    ↓
Mise à jour versionnée de la référence d’image dans Ansible
                    ↓
Validation de la version en environnement de test
                    ↓
Déclenchement manuel du déploiement sur lab-studio
                    ↓
Contrôles applicatifs et observation des métriques
```

1. **Vérifier le changement (CI).** Exécuter les tests de l’application, vérifier la configuration Compose et, si les fichiers d’infrastructure changent, la syntaxe Ansible. Un échec bloque la suite. Les tests d’une branche ne doivent pas disposer des secrets de déploiement.
2. **Construire et publier.** Après fusion, construire une image identifiée par le commit, la publier sur le NAS et conserver son digest. Cibler `linux/amd64` pour la tour ; une application destinée au Pi nécessiterait une image compatible avec son architecture. Les outils du runner doivent être sélectionnés par `mise`, comme pour le développement local.
3. **Enregistrer la version à livrer.** Mettre à jour la variable d’image correspondante dans le dépôt d’infrastructure avec le digest publié. Le composant `jarvis-exporter`, actuellement déclaré avec une construction locale dans Compose, devrait évoluer vers cette image publiée. Tester puis déployer la même image, sans la reconstruire entre les environnements.
4. **Déployer avec Ansible et Compose.** Après validation, le runner lance le déploiement de l’application concernée. Il faut prévoir une tâche ou un playbook adapté à ce périmètre pour éviter d’exécuter toute la configuration de la tour à chaque livraison. Un seul déploiement doit pouvoir modifier une cible à la fois.
5. **Vérifier le résultat.** Attendre les contrôles de santé et tester une fonction réelle de l’application. Prometheus/Grafana complètent ces contrôles ; ils ne remplacent pas les tests. Conserver les journaux du pipeline et l’association entre commit, digest et cible déployée.
6. **Prévoir le retour arrière.** Conserver l’ancien digest et sa configuration pour pouvoir les redéployer. Les volumes persistants restent à gérer séparément : une migration de base de données peut nécessiter une procédure spécifique et une sauvegarde restaurable.

Pour un logiciel tiers comme Grafana, il n’est généralement pas nécessaire de reconstruire le logiciel : le pipeline peut vérifier une version amont, la recopier dans le registry privé puis valider son déploiement.

## Où exécuter le pipeline ?

Une première étape serait un script reproductible lancé manuellement depuis WSL. Il automatiserait les opérations, mais deviendrait une intégration continue lorsqu’un moteur CI/CD le déclencherait systématiquement sur les changements Git.

La cible pourrait ensuite être une forge avec CI intégrée, ou un moteur CI compatible avec les dépôts Git existants, accompagné d’un runner Linux dans le homelab. Celui-ci aurait accès au Git et au registry du NAS, puis aux hôtes par SSH pour le déploiement. Le placer dans le réseau local éviterait de rendre SSH et le registry publics. Le moteur, le runner et leur emplacement restent à choisir ; Tailscale est une autre possibilité d’accès privé, encore exploratoire ici.

Les secrets de publication, SSH, sudo et Ansible Vault doivent être fournis par un mécanisme non interactif protégé. Le fonctionnement actuel avec saisie de mots de passe demande donc une adaptation. Séparer les droits de test, de publication et de déploiement, et faire confiance au certificat TLS du registry sur le runner. Un runner qui exécute du code non approuvé ne doit pas disposer d’un accès administrateur aux hôtes.

## Les schémas classiques en entreprise

Les entreprises adaptent leurs pipelines à la criticité des applications. Un parcours fréquent est : branche et revue de code, CI, publication d’un artefact versionné, déploiement en recette, tests d’intégration, puis mise en production et supervision.

- **Livraison continue :** la version validée est prête à être déployée, mais la mise en production conserve une validation humaine.
- **Déploiement continu :** la mise en production est automatique après réussite de tous les contrôles.
- **Avec Kubernetes et GitOps :** le pipeline publie l’image et met à jour la version souhaitée dans Git ; un contrôleur, comme Argo CD ou Flux, applique cette configuration au cluster.

Kubernetes et GitOps sont des options d’architecture. Une entreprise peut également livrer ses applications sur des VM avec Ansible et Compose. Les points structurants sont la reproductibilité, les contrôles, les droits d’accès, la traçabilité et la capacité à rétablir le service. Les [environnements de déploiement GitHub](https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments) illustrent les mécanismes de validation, de restriction des branches et de secrets par environnement.

## Comparaison : homelab et besoins professionnels

| Aspect | Homelab documenté aujourd’hui | Cible locale proposée | Pratiques et besoins professionnels courants |
|---|---|---|---|
| Code et changements | Git sur le NAS ; configuration dans ce dépôt | Branches, historique et vérifications avant fusion | Revues de code, branches protégées, responsabilités définies |
| Déclenchement | Commandes lancées depuis WSL | CI sur les changements Git ; déploiement manuel après validation | Déclencheurs et validations adaptés au risque, avec historique |
| Exécution | PC admin comme nœud de contrôle Ansible | Runner Linux avec outils fixés par `mise` | Runners isolés, reproductibles, entretenus et dimensionnés pour les équipes |
| Tests | Tests présents pour `jarvis-exporter` ; pas d’exécution CI identifiée | Tests automatiques et validation des configurations | Tests unitaires, d’intégration et fonctionnels ; contrôles de sécurité selon le contexte |
| Images | Registry privé ; procédure de publication et références par digest | Construction automatisée et lien commit → digest → déploiement | Artefacts conservés, contrôlés et promus entre environnements |
| Environnements | Pas de recette séparée identifiée | Instance de test avec ports, volumes et données distincts | Séparation des environnements, des données et des accès ; recette représentative |
| Déploiement | Playbooks Ansible et Compose | Déploiement ciblé, sérialisé, avec contrôles applicatifs | Automatisation contrôlée ; stratégies limitant les interruptions selon les exigences |
| Secrets et accès | SSH, sudo, Ansible Vault et comptes du registry | Secrets fournis au runner et droits distincts par étape | Identités dédiées, moindre privilège, rotation et audit des accès |
| Exploitation | Prometheus/Grafana ; retour au digest précédent documenté | Résultat du déploiement, métriques et retour arrière testé | Alertes, suivi des incidents, objectifs de disponibilité et procédures de reprise |
| Sauvegardes | Procédure actuelle et test de restauration encore à définir | Sauvegarder Git, registry et données ; tester la restauration | Rétention et restauration validées selon les pertes et délais acceptables |
| Infrastructure | Ansible pour les hôtes et Compose pour les services | Pipelines adaptés aux fichiers modifiés | Terraform si pertinent pour les ressources ; Ansible pour la configuration ; moteur de déploiement adapté |

Le premier écart à combler est l’automatisation vérifiable de la livraison : tests à chaque changement, image identifiable, déploiement contrôlé et reprise testée. Terraform deviendrait utile pour provisionner des ressources supplémentaires ; Kubernetes répondrait à d’autres besoins de gestion des applications. Aucun des deux n’est un préalable à ce pipeline local.

Références complémentaires : [intégration continue avec GitHub Actions](https://docs.github.com/en/actions/get-started/continuous-integration), [déploiement continu](https://docs.github.com/en/actions/get-started/continuous-deployment), [utilisation de Compose en production](https://docs.docker.com/compose/how-tos/production/).

# Homelab IA local — état des lieux et pistes d’architecture

> Document de contexte destiné à être intégré au projet homelab et à servir de point de départ pour une nouvelle conversation Codex.

## 1. Objectif général

Transformer l’infrastructure existante en plateforme d’IA locale capable de faire fonctionner :

- un assistant vocal Jarvis disponible 24 h/24 ;
- des modèles de langage locaux ;
- des agents et leurs outils ;
- du RAG, des embeddings et de l’indexation documentaire ;
- éventuellement des expérimentations sur de très grands modèles MoE avec Colibrì ;
- le tout en conservant une séparation entre les services stables et les machines d’expérimentation.

L’objectif n’est plus le gaming. La tour équipée d’une RTX 4090 devient `jarvis-core`, le principal serveur de calcul IA.

## 2. Infrastructure actuelle

| Machine | Matériel | Rôle actuel ou prévu |
|---|---|---|
| `jarvis-central` | Ryzen 5, 32 Go de RAM, RTX 2060 6 Go | Pipeline vocal Jarvis, Home Assistant, Wyoming, Ollama léger et point d’entrée disponible 24 h/24 |
| `jarvis-core` | Ryzen 9 7900X, 64 Go de RAM, RTX 4090 24 Go, SSD NVMe 4 To | Moteur principal d’inférence LLM et serveur de calcul IA |
| `nas` | Raspberry Pi 4, 8 Go | Serveur Git, documentation, mémoire des agents et partage familial SMB |
| `pc-admin` | Portable Asus ROG | Administration du homelab |

## 3. Configuration exacte de `jarvis-core`

### Processeur

- AMD Ryzen 9 7900X
- 12 cœurs / 24 threads
- Architecture Zen 4
- Support AVX-512
- Jusqu’à 5,6 GHz
- TDP de 170 W

### Carte graphique

- Gigabyte AORUS GeForce RTX 4090 XTREME WATERFORCE
- 24 Go de GDDR6X
- Refroidissement liquide avec radiateur de 360 mm
- Modèle `GV-N4090EAORUSX W-24GD`

### Mémoire vive

- Corsair Vengeance RGB DDR5
- 64 Go, sous la forme de 2 × 32 Go
- DDR5-6000 CL30
- Profil AMD EXPO
- Référence `CMH64GX5M2B6000Z30`

### Carte mère

- MSI MAG B650 TOMAHAWK WIFI
- Socket AM5
- Deux emplacements physiques PCIe x16, mais le second n’est câblé qu’en PCIe 4.0 x2
- Trois emplacements M.2
- Réseau 2,5 GbE

### Stockage

- WD Black SN850X 4 To
- NVMe PCIe 4.0
- Jusqu’à environ 7,3 Go/s en lecture séquentielle annoncée

### Alimentation

- Corsair RM1000x
- 1 000 W
- ATX 3.1 et PCIe 5.1
- Connecteur natif 12V-2x6
- Certification Cybenetics Gold

### Matériel disponible mais non utilisé

- 32 Go de DDR5 Corsair Vengeance, 2 × 16 Go, 7200 MHz CL34, profil Intel XMP ;
- carte mère ASUS PRIME B650-PLUS.

## 4. Diagnostic honnête de la tour

`jarvis-core` est une excellente machine d’IA locale mono-GPU. Elle est particulièrement adaptée à :

- l’inférence de modèles tenant entièrement ou presque entièrement dans 24 Go de VRAM ;
- l’utilisation de modèles quantifiés ;
- les modèles multimodaux ;
- la génération d’images ;
- la transcription et la synthèse vocale ;
- les embeddings et le reranking ;
- les petits entraînements et les LoRA ;
- l’exécution simultanée d’agents, d’outils et de services associés.

Ses principales limites sont :

- les 24 Go de VRAM, malgré la puissance de calcul très élevée de la RTX 4090 ;
- la mémoire système en double canal, qui limite les performances des gros modèles déportés en RAM ;
- la carte mère B650, mal adaptée à une configuration multi-GPU ;
- l’absence de NVLink sur la RTX 4090 ;
- l’alimentation de 1 000 W, excellente pour la configuration actuelle mais insuffisamment confortable pour ajouter une deuxième carte très énergivore.

Cette tour peut être utilisée à 100 % de son potentiel, mais pas nécessairement en maintenant chaque composant à 100 % d’utilisation en permanence. Son intérêt vient aussi de sa réserve de capacité, de sa faible latence et de sa capacité à absorber plusieurs tâches simultanées.

## 5. Le Ryzen 9 7900X est-il inutile ?

### Pour de l’inférence pure en VRAM

Si `jarvis-core` ne fait qu’exécuter un modèle entièrement chargé dans les 24 Go de la RTX 4090, le Ryzen 9 est effectivement surdimensionné. Un Ryzen 5 7600 ou un Ryzen 7 7700 donnerait souvent un débit de génération assez proche, car le GPU réalise l’essentiel du calcul.

Dans ce scénario très limité, une partie importante des 12 cœurs resterait inutilisée.

### Pour un véritable serveur d’IA et d’agents

Dans une architecture complète, le Ryzen 9 peut devenir le plan d’exécution général de la plateforme. Il peut prendre en charge :

- les conteneurs Docker ou Podman des agents ;
- les outils appelés par les modèles ;
- les serveurs MCP ;
- l’exécution de code en environnement isolé ;
- l’extraction et la conversion de documents ;
- la construction et la mise à jour des index RAG ;
- les bases vectorielles ;
- les embeddings ou le reranking sur CPU lorsque le GPU est occupé ;
- la préparation, la conversion et la quantification des modèles ;
- plusieurs requêtes concurrentes ;
- les experts MoE calculés sur CPU dans Colibrì ;
- les services d’orchestration, de journalisation et de supervision.

Le CPU n’est donc pas inutile. Il le deviendrait seulement si la machine était réduite au rôle de simple boîtier autour de la RTX 4090.

Il n’est pas nécessaire de chercher artificiellement à saturer le processeur. Des cœurs disponibles apportent de la réactivité et évitent que les outils, l’indexation ou les services d’agents ralentissent l’inférence.

## 6. Architecture fonctionnelle recommandée

```text
Microphones, interfaces et Home Assistant
                    |
                    v
          +-------------------+
          |  jarvis-central   |
          |-------------------|
          | Point d’entrée    |
          | Pipeline vocal    |
          | Wyoming           |
          | Modèle léger      |
          | Services 24 h/24  |
          +---------+---------+
                    |
        Requête simple ou lourde
                    |
          +---------v---------+
          |   jarvis-core     |
          |-------------------|
          | RTX 4090 : LLM    |
          | Ryzen 9 : agents  |
          | Outils et RAG     |
          | Indexation        |
          | Services MCP      |
          | Expérimentations  |
          +---------+---------+
                    |
                    v
          +-------------------+
          |       NAS         |
          |-------------------|
          | Git et documents  |
          | Mémoire durable   |
          | Sauvegardes       |
          | Partages SMB      |
          +-------------------+
```

### `jarvis-central`

Cette machine doit rester le point d’entrée stable et disponible 24 h/24 :

- gestion du pipeline vocal ;
- interaction avec Home Assistant ;
- détection du mot-clé et services Wyoming ;
- traitement local des demandes simples avec un petit modèle ;
- routage des demandes complexes vers `jarvis-core` ;
- maintien d’un service minimal lorsque `jarvis-core` redémarre ou sert aux expérimentations.

Il est pertinent de ne pas déplacer tout le système Jarvis sur la grosse tour. Cette séparation évite qu’une mise à jour de modèle, une saturation GPU ou une expérience fasse tomber la domotique et l’interface vocale.

### `jarvis-core`

Cette machine peut réunir deux plans complémentaires :

1. **Plan d’inférence GPU**
   - grands modèles de langage quantifiés ;
   - modèles multimodaux ;
   - génération d’images ;
   - transcription ou synthèse vocale lourde ;
   - embeddings GPU lorsque cela est pertinent.

2. **Plan d’exécution CPU**
   - agents ;
   - outils ;
   - RAG ;
   - indexation ;
   - bases vectorielles actives ;
   - services MCP ;
   - traitement documentaire ;
   - isolation et exécution de code ;
   - orchestration des appels au GPU.

### `nas`

Le Raspberry Pi peut rester la couche de persistance et de sauvegarde :

- dépôts Git ;
- documentation ;
- mémoire durable des agents ;
- corpus documentaires ;
- sauvegardes ;
- partage SMB.

Les charges actives et intensives, comme l’indexation massive ou une base vectorielle sollicitée en permanence, gagneraient à s’exécuter sur `jarvis-core`. Les données et sauvegardes resteraient stockées ou répliquées sur le NAS.

## 7. Répartition possible des requêtes

Le routeur de `jarvis-central` pourrait classer les requêtes :

| Type de requête | Destination recommandée |
|---|---|
| Commande domotique simple | `jarvis-central` |
| Conversation courte et peu complexe | Petit modèle sur la RTX 2060 |
| Raisonnement complexe | Modèle principal sur la RTX 4090 |
| Question nécessitant le RAG | `jarvis-core`, puis accès aux documents du NAS |
| Appel d’outil ou exécution de code | Workers CPU de `jarvis-core` |
| Traitement documentaire lourd | `jarvis-core` |
| Expérience Colibrì ou très grand modèle | `jarvis-core`, dans un service isolé |

Le routage peut commencer avec des règles simples. Il n’est pas nécessaire d’installer immédiatement un classificateur sophistiqué.

## 8. Utilisation de la mémoire

### Configuration recommandée actuellement

Conserver les 64 Go en 2 × 32 Go à 6000 MT/s CL30 avec EXPO est la configuration la plus simple et la plus performante.

### Test possible avec les barrettes disponibles

Les deux barrettes de 16 Go pourraient porter la machine à 96 Go, mais :

- elles utilisent un profil Intel XMP et non AMD EXPO ;
- elles ne sont pas identiques au kit de 64 Go ;
- quatre barrettes DDR5 chargent davantage le contrôleur mémoire ;
- une fréquence de 6000 MT/s est très improbable avec les quatre barrettes ;
- la fréquence pourrait devoir être abaissée à 4800 MT/s, voire moins selon la stabilité.

Ce mélange peut néanmoins être testé gratuitement si Colibrì ou de gros modèles déportés en RAM deviennent une priorité :

1. désactiver EXPO et XMP ;
2. commencer à 4800 MT/s ;
3. effectuer un test mémoire prolongé ;
4. mesurer les performances réelles avec 64 Go rapides puis 96 Go plus lents ;
5. conserver 96 Go seulement si la capacité supplémentaire réduit suffisamment les accès au SSD.

Pour une évolution propre et durable, un kit assorti de 2 × 64 Go serait préférable à quatre barrettes mélangées.

## 9. Stockage et emplacement M.2

Le SN850X est un bon SSD pour les modèles et les caches. Il doit idéalement être placé dans `M2_1` ou `M2_2`.

Sur la MSI MAG B650 TOMAHAWK WIFI, `M2_3` partage de la bande passante avec le second emplacement PCIe. Utiliser simultanément ces deux emplacements peut réduire leur connexion à deux lignes PCIe.

Pour les charges de type Colibrì, le débit séquentiel annoncé n’est pas le seul indicateur important. Il faut aussi mesurer :

- les lectures aléatoires de blocs d’environ 19 Mo ;
- la latence ;
- les performances avec plusieurs lectures en parallèle ;
- les températures et le throttling du SSD.

## 10. Alimentation et évolution GPU

La RM1000x est très bien dimensionnée pour la RTX 4090 et le Ryzen 9 7900X.

Une charge réaliste de la machine complète peut se situer approximativement entre 680 et 780 W lors d’un travail intensif simultané du GPU et du CPU. L’alimentation conserve donc une marge correcte avec la configuration actuelle.

En revanche, ajouter dans la même tour une RTX 3090 de 350 W ou une carte serveur de 250 W serait peu recommandé :

- marge électrique insuffisante ou trop faible ;
- charge thermique importante ;
- deuxième emplacement PCIe limité à deux lignes ;
- contraintes physiques et de refroidissement ;
- complexité accrue pour un gain parfois faible.

Si un deuxième GPU devient nécessaire, une seconde machine dédiée sera probablement plus cohérente que l’ajout dans `jarvis-core`.

## 11. RTX 3090 et RTX 4090

La RTX 3090 et la RTX 4090 disposent toutes deux de 24 Go de VRAM.

La RTX 4090 apporte surtout :

- beaucoup plus de puissance de calcul ;
- une architecture plus récente ;
- de meilleurs Tensor Cores ;
- une meilleure efficacité ;
- des performances supérieures pour l’inférence, la génération d’images et l’entraînement.

Elle n’apporte cependant aucune capacité mémoire supplémentaire. Pour l’IA locale, cela signifie qu’un modèle qui ne tient pas dans les 24 Go d’une RTX 3090 ne tiendra pas davantage dans une RTX 4090.

La RTX 3090 d’occasion reste donc souvent intéressante pour maximiser le nombre de gigaoctets de VRAM par euro. La RTX 4090 est meilleure lorsque le modèle tient dans 24 Go et que la vitesse de calcul compte.

## 12. Colibrì et les très grands modèles MoE

Colibrì est un moteur d’inférence destiné à GLM-5.2, un modèle MoE d’environ 744 milliards de paramètres, quantifié sur disque à environ 372 Go.

Le principe n’est pas de charger et décharger un expert depuis la VRAM à chaque token :

- les experts fréquemment utilisés peuvent rester en VRAM ;
- d’autres experts sont conservés en RAM ;
- les experts froids restent sur le SSD ;
- le routeur sélectionne seulement quelques experts par couche ;
- un expert absent est lu depuis le SSD vers la RAM et calculé sur CPU ;
- les experts chauds peuvent être épinglés en VRAM à des moments sûrs.

Le chemin critique ne consiste donc pas à transférer environ 19 Mo d’expert vers le GPU à chaque activation. Cela remplacerait simplement le goulot d’étranglement SSD par un goulot d’étranglement PCIe.

### Conséquence pour `jarvis-core`

Dans Colibrì, le Ryzen 9 devient utile :

- calcul des experts conservés en RAM ;
- exécution parallèle sur 12 cœurs ;
- utilisation d’AVX-512 ;
- préparation et orchestration des lectures ;
- gestion du cache d’experts.

La RTX 4090 accélère les parties résidentes et les experts chauds, mais elle ne sera pas nécessairement saturée. La limitation principale peut devenir la bande passante de la RAM, la latence du SSD ou le taux de défauts de cache.

Avec 64 Go de RAM, Colibrì reste surtout une plateforme expérimentale. Il ne faut pas s’attendre à l’expérience interactive d’un modèle entièrement chargé en VRAM.

### Positionnement recommandé

- Utiliser un moteur classique comme Ollama, llama.cpp ou vLLM pour le service quotidien.
- Réserver Colibrì aux expériences sur de très grands modèles MoE.
- Exécuter Colibrì dans un service séparé afin qu’il ne compromette pas le fonctionnement normal de Jarvis.

## 13. Idée de cluster d’experts

Une extension possible de Colibrì consisterait à conserver les experts sur d’autres machines :

1. `jarvis-core` calcule le chemin dense et le routage ;
2. le routeur choisit les experts nécessaires ;
3. la petite activation intermédiaire est envoyée aux machines qui possèdent ces experts ;
4. les workers calculent les experts localement ;
5. ils renvoient les résultats pondérés ;
6. `jarvis-core` poursuit la couche suivante.

Il est préférable de déplacer les activations, de l’ordre de quelques kilo-octets, plutôt que les poids d’experts d’environ 19 Mo.

Un cluster de Jetson Orin Nano pourrait techniquement servir de groupe de workers, mais il présenterait plusieurs limites :

- seulement 8 Go de mémoire unifiée par machine ;
- experts principalement stockés sur NVMe ;
- Ethernet 1 Gb/s intégré ;
- synchronisation réseau à chaque couche MoE ;
- coût total proche de 5 000 € pour dix machines ;
- complexité logicielle et opérationnelle importante.

Pour un budget équivalent, des GPU d’occasion dotés de 24 Go peuvent être plus simples et plus rapides. Le cluster Jetson reste toutefois intéressant comme projet de recherche distribué à faible consommation.

## 14. Cartes graphiques d’occasion envisagées

Les prix varient fortement selon la région et la période, mais les familles pertinentes sont :

| Carte | VRAM | Intérêt principal | Limites |
|---|---:|---|---|
| Tesla P100 PCIe | 16 Go | VRAM peu coûteuse | Ancienne génération, refroidissement passif, support logiciel vieillissant |
| Tesla P40 | 24 Go | Capacité de 24 Go à faible prix | Pascal, pas de Tensor Cores modernes, refroidissement passif, support CUDA limité aux anciennes branches |
| GTX 1080 Ti | 11 Go | Prix d’occasion faible | Capacité insuffisante pour un cluster dense en VRAM |
| RTX 2080 Ti | 11 Go | Tensor Cores Turing | Seulement 11 Go |
| Quadro RTX 6000 | 24 Go | Format professionnel plus pratique en multi-GPU | Plus chère |
| RTX 3090 | 24 Go | Meilleur compromis pratique, rapide et encore moderne | Environ 350 W, souvent volumineuse |
| Quadro RTX 8000 | 48 Go | Forte densité mémoire par carte | Prix d’occasion généralement élevé |

Il n’existe pas de « RTX 1090 ». La carte généralement recherchée pour 24 Go à prix raisonnable est la RTX 3090.

Pour un futur nœud GPU :

- **expérimentation au coût minimal** : Tesla P40, en acceptant les contraintes ;
- **solution pratique et performante** : RTX 3090 ;
- **forte densité dans un châssis multi-GPU** : cartes professionnelles de 24 ou 48 Go, si leur prix est réellement intéressant.

## 15. Priorités recommandées

### Priorité 1 — rendre `jarvis-core` utile sans achat

- Installer le moteur d’inférence principal.
- Exposer une API locale compatible OpenAI.
- Faire router les requêtes lourdes de `jarvis-central` vers `jarvis-core`.
- Réserver la RTX 4090 au calcul en utilisant la sortie vidéo de la carte mère si un écran est nécessaire.
- Mettre en place les workers CPU pour les outils, le RAG et le traitement documentaire.

### Priorité 2 — instrumenter avant de modifier le matériel

Mesurer :

- VRAM utilisée ;
- RAM utilisée ;
- débit en tokens/s ;
- temps avant le premier token ;
- utilisation GPU ;
- utilisation par cœur CPU ;
- débit et latence du SSD ;
- trafic réseau ;
- consommation électrique ;
- températures ;
- latence complète entre la voix de l’utilisateur et la réponse.

Ces mesures permettront de savoir si la prochaine limite est la VRAM, la RAM, le stockage, le CPU ou le réseau.

### Priorité 3 — séparer les services stables et expérimentaux

- service quotidien de Jarvis ;
- moteur LLM principal ;
- workers d’agents ;
- services RAG ;
- expérimentations Colibrì ;
- supervision et journalisation.

Chaque bloc devrait pouvoir redémarrer sans rendre indisponible tout le système.

### Priorité 4 — repousser l’achat de matériel

La machine actuelle est déjà puissante. Avant d’acheter un deuxième GPU ou un cluster, il est préférable de vérifier :

- quels modèles sont réellement nécessaires ;
- combien de requêtes simultanées doivent être servies ;
- si 24 Go de VRAM constituent réellement la limite ;
- si le besoin concerne la capacité mémoire, le débit ou la disponibilité ;
- si un nœud supplémentaire apporterait davantage qu’une optimisation logicielle.

## 16. Questions à traiter dans la prochaine phase

1. Quel moteur d’inférence utiliser sur `jarvis-core` : Ollama, llama.cpp, vLLM, SGLang ou combinaison de plusieurs moteurs ?
2. Quels modèles doivent rester chargés en permanence ?
3. Quel modèle léger doit fonctionner sur `jarvis-central` ?
4. Comment router automatiquement les requêtes entre les deux machines ?
5. Où placer la base vectorielle et comment répliquer ses données sur le NAS ?
6. Comment isoler les outils exécutés par les agents ?
7. Quel protocole utiliser entre Jarvis, les agents et les moteurs d’inférence ?
8. Comment organiser la mémoire à court terme, la mémoire à long terme et la documentation Git ?
9. Quelle stratégie de secours appliquer si `jarvis-core` est indisponible ?
10. Quels tableaux de bord et métriques mettre en place ?
11. Colibrì doit-il rester un laboratoire séparé ou devenir un backend optionnel de Jarvis ?
12. À partir de quelles mesures un achat de RAM ou d’un second nœud GPU devient-il justifié ?

## 17. Conclusion

Le Ryzen 9 7900X n’est pas inutile, mais son intérêt dépend de l’architecture logicielle.

Si `jarvis-core` sert uniquement à lancer Ollama avec un modèle entièrement chargé dans la RTX 4090, le processeur sera largement sous-utilisé. Si la machine devient le moteur général des agents — inférence, outils, RAG, indexation, isolation, orchestration et expérimentations — alors le 7900X est cohérent et apporte une réserve utile.

La meilleure évolution immédiate n’est probablement pas l’achat d’une deuxième carte graphique. Elle consiste à exploiter la séparation déjà présente :

- `jarvis-central` comme interface stable et disponible ;
- `jarvis-core` comme serveur de calcul IA et d’agents ;
- le NAS comme couche de persistance et de sauvegarde.

Cette architecture valorise le matériel existant, limite les dépenses et laisse ensuite les mesures réelles guider les futurs achats.

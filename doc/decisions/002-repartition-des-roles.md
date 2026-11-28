# 002 — Répartir les rôles entre l’état, l’orchestration et le calcul

**Statut :** expérimental. L’architecture est en cours de montage et sera réévaluée après les premiers essais.
**Date :** novembre 2026.

## Contexte

- Le homelab compte une seule grosse carte graphique, la RTX 4090 de `lab-forge`. `lab-studio` a une RTX 2060 de 6 Gio.
- Presque tout l’état du homelab est déjà sur le NAS. Le second cerveau y est stocké et versionné dans Git.
- `lab-forge` servira à l’inférence au quotidien, mais aussi à tester d’autres modèles pour voir comment ils se comportent dans cette architecture.
- Toutes les requêtes ne sont pas vocales : le travail et la gestion du second cerveau passent par du texte, sans STT ni TTS.

## Décision

| Machine | Rôle | Conséquence |
|---|---|---|
| NAS | **L’état** : dépôts Git, dont le second cerveau, partages Samba et registry d’images | Les données à sauvegarder sont là, et seulement là |
| `lab-studio` | **L’orchestration**, toujours allumée : le harness, Home Assistant et sa chaîne vocale, un petit modèle sur la 2060 pour les traitements légers | Point d’entrée de toutes les requêtes |
| `lab-forge` | **Le calcul, sans état** : moteur LLM sur la 4090 pour les gros modèles, et les essais de modèles | Peut être réinstallé sans perte : les modèles se retéléchargent |

- **Le harness est le point d’entrée unique.** Une requête texte va directement du harness au LLM. Une requête vocale entre par Home Assistant, qui fait le STT, appelle le harness comme agent de conversation, puis fait le TTS. La domotique est un outil que le harness appelle chez Home Assistant.
- **L’API compatible OpenAI est celle du moteur.** Le harness appelle directement `/v1/chat/completions` sur Ollama. Changer de moteur (vLLM, llama.cpp…) ne demande de changer que l’adresse ou le nom du modèle, pas le harness.

## Compromis acceptés pour l’instant

- **L’inférence lourde est indisponible pendant les essais** de modèles sur `lab-forge`.
- **Pas de passerelle** entre le harness et les moteurs.
- **Pas d’authentification** sur l’API des moteurs : Ollama n’en a pas, et tout le réseau Homelab peut l’appeler. La sécurité sera traitée quand la fiabilité du système sera connue. Voir [Sécurité des accès](../exploitation/securite.md).

## Alternatives écartées

- **Une couche serveur dédiée sur `lab-forge`** pour fournir l’API OpenAI : le moteur la fournit déjà.
- **Une passerelle dès maintenant**, comme LiteLLM. Elle apporterait une adresse unique pour les deux GPU, une bascule vers la 2060 quand `lab-forge` est indisponible, et des journaux par modèle. Si elle devient utile, elle ira sur `lab-studio`, toujours allumé et qui voit les deux GPU, plutôt que sur `lab-forge`.
- **Home Assistant comme orchestrateur de toutes les requêtes** : les requêtes texte n’ont pas besoin de la chaîne vocale, et deux orchestrateurs auraient chacun leurs prompts et leurs outils.

## Conséquences

- Le profil de `lab-forge` reste court : Docker, pilote NVIDIA, accès au registry et moteur LLM.
- Le harness et ses dépendances vont dans le profil de `lab-studio`.
- Les parcours prévus sont décrits dans [Parcours des requêtes](../architecture/parcours-des-requetes.md), chacun marqué *en place* ou *cible*.

# Routeur multi-modèles — orchestrateur vocal (conception)

> Évolution envisagée de [jarvis.md](jarvis.md) §12 : remplacer le pipeline
> vocal linéaire par un aiguilleur qui route chaque demande vers le modèle
> le plus adapté.
> Dernière mise à jour : 10 juillet 2026
> Statut : **🧠 brainstorming — document de travail, rien n'est décidé.**
> À concevoir ensemble ; ce squelette pose le problème et les questions.

---

## 1. L'intention

Aujourd'hui, toute demande vocale suit le même couloir :
`wake word → STT → LLM texte → TTS`. Ça marche, mais :

- le passage systématique par le texte **aplatit la communication**
  (intonation, hésitations, naturel perdus) et additionne les latences ;
- un même modèle (Qwen3 4B) traite tout — trop juste pour du raisonnement
  élaboré, sur-dimensionné en cérémonie pour un « quelle heure est-il ? ».

Cible : un **orchestrateur** qui reçoit l'audio et choisit la voie :

| Type de demande | Voie | Bénéfice |
|---|---|---|
| Légère / conversationnelle | Modèle **audio-natif** (speech-to-speech, pas de STT/TTS) | Fluidité, authenticité, latence minimale |
| Technique / réflexion | STT → **LLM de raisonnement** → TTS | Qualité de réponse |
| Domotique | Intent → **HA** (API/MCP) | Rapidité, fiabilité (existant) |

## 2. Schéma cible (première esquisse)

```
[ Satellites (Wyoming) ] ──audio──► [ ORCHESTRATEUR ]
                                       │ classifie la demande
                     ┌─────────────────┼─────────────────────┐
                     ▼                 ▼                     ▼
              modèle audio-natif   STT → LLM réflexion   Home Assistant
              (speech-to-speech)   → TTS                 (domotique, API/MCP)
```

Invariant : **les satellites ne changent pas** (Wyoming, protocole ouvert) ;
HA reste le back-end domotique. Seule la couche d'orchestration change.

## 3. Questions à trancher (matière de la session de conception)

1. **Le classifieur** : comment décider « léger vs technique » *avant*
   d'avoir compris la demande ? (transcription rapide + mini-modèle ?
   premier passage audio-natif qui escalade ? mots-clés ? latence cible ?)
2. **Le modèle audio-natif** : lequel (Moshi/Kyutai, Qwen-Omni, autres ?),
   quelle VRAM exigée, qualité du français ?
3. **Le LLM de réflexion** : local (gros GPU à acquérir) ou fallback cloud
   (contredit le 100 % local — acceptable pour certaines demandes ?) ?
4. **Où vit l'orchestrateur** : conteneur sur jarvis-central ? Implémente-t-il
   le protocole Wyoming côté satellites (transparent pour eux) ?
5. **Le wake word** reste-t-il openWakeWord en amont, inchangé ?
6. **Continuité de conversation** : une demande légère qui devient technique
   en cours de dialogue — l'orchestrateur peut-il transférer le contexte ?
7. **Build vs adopt** : la communauté aura-t-elle produit une brique de
   routing d'ici là ? (à surveiller — veille §10 de jarvis.md)
8. **Mémoire partagée** : les trois voies doivent-elles lire/écrire la même
   mémoire OKF (profils, préférences) pour rester « un seul Jarvis » ?

## 4. Contraintes connues dès maintenant

- **VRAM** : les modèles audio-natifs locaux dépassent largement les 6 Go
  de la RTX 2060 → ce projet dépend du « scale vertical » (GPU plus gros).
- **HA n'est pas extensible pour ça** : son pipeline Assist est centré
  texte ; l'orchestrateur vit *devant* HA, pas dedans.
- **Ne pas fermer la porte** : chaque brique ajoutée d'ici là doit rester
  découplée (services indépendants, protocoles ouverts) — c'est déjà le cas.

## 5. Pré-requis avant d'ouvrir le chantier

- [ ] Phases 1–3 de [jarvis.md](jarvis.md) suffisamment avancées (satellites,
      mémoire, couche agentique).
- [ ] GPU dimensionné pour un modèle audio-natif.
- [ ] Veille : maturité des modèles speech-to-speech FR et des briques de
      routing communautaires.

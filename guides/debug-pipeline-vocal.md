# Guide — déboguer le pipeline vocal

> Méthodes éprouvées (session du 10 juillet 2026, premier « Hey Jarvis »
> réussi) pour diagnostiquer la chaîne satellite → wake word → STT → LLM →
> TTS. Machine : `jarvis-central`
> (voir [../serveurs/jarvis-central/etat.md](../serveurs/jarvis-central/etat.md)).

---

## 1. Le pipeline, et où ça peut casser

```
micro XVF3800 ─► wyoming-satellite ─► openwakeword ─► HA (pipeline Assist)
                     (hôte)             (détection)      ├─► whisper (STT)
                                                         ├─► ollama  (LLM)
                                                         └─► piper   (TTS)
                                                              │
enceinte ◄── aplay (satellite) ◄─────────────────────────────┘
```

Stratégie : localiser **l'étage** fautif avant de régler quoi que ce soit.
Chaque étage a son outil d'observation, du matériel vers le logiciel.

---

## 2. Étage matériel (USB / ALSA)

```bash
lsusb                     # la carte est-elle vue par l'USB ? (chercher Seeed/XMOS)
arecord -l                # est-elle une carte de capture ALSA ? (noter card N)
cat /proc/asound/cards    # vue noyau des cartes son
```

- `arecord -l` vide alors que `lsusb` voit la carte → modules son manquants
  (Ubuntu Server) : `sudo apt install linux-modules-extra-$(uname -r)` + reboot,
  ou problème de droits (groupe `audio`).
- **Test d'enregistrement** (satellite ÉTEINT — la carte ne se partage pas,
  sinon `Device or resource busy`) :

```bash
arecord -D plughw:2,0 -f S16_LE -r 16000 -c 1 -d 5 test.wav   # 2 = numéro de carte
```

> Le numéro de carte est positionnel (peut changer entre boots). Pour les
> configs durables, adresser **par nom** : `plughw:CARD=Array,DEV=0`
> (le nom est dans la sortie d'`arecord -l`).

- **Vu-mètre temps réel** (niveau micro à l'œil) :

```bash
arecord -D plughw:2,0 -V mono -f S16_LE -r 16000 -c 1 /dev/null
```

- **Test enceinte** : `aplay -D plughw:2,0 /usr/share/sounds/alsa/Front_Center.wav`
- `alsamixer -c 2` : F4 = vue capture. Le XVF3800 n'expose pas de gain de
  capture (traitement dans la puce XMOS) — l'amplification se fait au
  niveau du satellite (§3).

---

## 3. Étage satellite (wyoming-satellite)

Lancer avec `--debug` : chaque événement du protocole s'affiche
(`Detection`, `Streaming audio`, `run-pipeline`, `transcript`, `synthesize`…).
La dernière ligne visible dit **où la chaîne s'arrête**.

Options de diagnostic et de réglage :

| Option | Usage |
|---|---|
| `--debug` | trace tous les événements Wyoming |
| `--debug-recording-dir /tmp/sat-debug` | **enregistre en .wav ce que le pipeline entend réellement** (flux wake word + flux envoyé au STT). L'outil de vérité : on écoute ce que Whisper reçoit. À réserver au débogage. |
| `--mic-volume-multiplier 2.0` | amplifie le micro (notre carte sort un niveau faible) |
| `--mic-auto-gain 0-31` | gain automatique, alternative au multiplicateur |

---

## 4. Étage wake word (openwakeword)

```bash
docker logs -f openwakeword
```

- Ajouter `--debug` à la commande du conteneur : montre les connexions
  clients et chaque détection (`Detected hey_jarvis at …`).
- Ajouter `--debug-probability` : logge le score de détection en continu
  (0 à 1, seuil de déclenchement = 0,5 par défaut). Si les lignes sont
  noyées : `docker logs -f openwakeword 2>&1 | grep -iE 'prob|detect'`.
  Lecture : max ~0,4 en parlant = presque — baisser `--threshold` ou monter
  le gain micro ; ~0 = le flux audio n'arrive pas ou est inaudible.
- **Prononciation** : le modèle `hey_jarvis` est entraîné sur des voix
  anglaises → « **héï djarvis** » fonctionne nettement mieux qu'un
  « hé Jarvis » à la française.
- Après une détection, ~5 s de période réfractaire (pas de redéclenchement).

---

## 5. Étage Home Assistant (pipeline Assist)

- **Le débogueur Assist** — l'outil principal : Paramètres → Assistants
  vocaux → carte du pipeline → menu ⋮ → **Déboguer**. Chaque exécution y est
  détaillée étape par étape : réveil, transcription Whisper, réponse LLM,
  synthèse TTS, avec durées et erreurs.
  ⚠️ Le débogueur est **par pipeline** : si une exécution semble absente,
  vérifier les autres pipelines du sélecteur (l'appareil est peut-être
  rattaché au mauvais assistant — voir l'entité « Assistant » sur la page
  de l'appareil Wyoming).
- **Logs détaillés à chaud** (sans redémarrage) : Outils de développement →
  Actions → `logger.set_level` :

```yaml
homeassistant.components.assist_pipeline: debug
homeassistant.components.wyoming: debug
```

  puis lire Paramètres → Système → Journaux.

---

## 6. Étage LLM / TTS

```bash
# Ollama répond-il ? (l'API qu'utilise HA)
curl http://localhost:11434/api/generate -d '{"model":"qwen3:4b-instruct-2507-q4_K_M","prompt":"test","stream":false}'

# Le GPU travaille-t-il pendant une génération ?
nvidia-smi        # processus ollama, ~3 Go VRAM ; ~95 tok/s = GPU, 10-20 = CPU
```

TTS seul : Outils de développement → Actions → `tts.speak`.

---

## 7. Signatures connues (symptôme → diagnostic)

| Symptôme | Diagnostic |
|---|---|
| Transcription « *Sous-titres réalisés par la communauté d'Amara.org* » (ou autre phrase de sous-titrage) | **Whisper a reçu du silence ou un signal quasi inaudible** — hallucination classique. Causes : rien dit après le réveil, ou niveau micro trop faible (→ `--mic-volume-multiplier`). |
| Wake word jamais détecté, LED du XVF réactives | Les LED = DoA de la puce, indépendantes du pipeline. Vérifier prononciation anglaise, puis scores `--debug-probability`. |
| `Device or resource busy` sur arecord | La carte est déjà ouverte (satellite en route). Un seul lecteur à la fois. |
| Satellite s'arrête à `run-pipeline`, rien après | HA n'exécute pas le pipeline : appareil rattaché au mauvais assistant, ou erreur côté HA (→ §5). |
| Réponses vocales en anglais | Instructions par défaut de l'intégration Ollama (anglaises) — personnaliser le prompt (voir etat.md §2.2). |
| Réponses interminables à l'oral | Le pipeline utilisé n'a pas les instructions « bref » — vérifier quel assistant l'appareil utilise. |

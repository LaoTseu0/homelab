"""Gestion du contexte : que faire quand l'historique devient trop long ?

Le probleme, constate avec le compteur de 02_chat.py : l'historique est
renvoye EN ENTIER a chaque tour, donc le contexte grossit sans fin. Deux
strategies classiques pour le contenir :

  - TRONCATURE : jeter les vieux messages. Simple, brutal — le modele
    devient amnesique sur le debut de la conversation.
  - COMPACTION : demander au modele de RESUMER les vieux echanges, et
    remplacer ceux-ci par le resume. On garde l'essentiel, on perd le
    detail. (C'est ce que subit Claude dans ses longues sessions.)

Le script detecte le depassement d'un seuil de tokens et applique la
strategie choisie AVANT l'appel suivant. Le seuil est volontairement bas
pour declencher vite en test.

Nouveautes Python : slicing de liste (messages[-4:]), join sur une
expression generatrice, NotImplementedError, len().
"""

import httpx

OLLAMA_URL = "http://192.168.1.57:11434"
MODEL = "qwen3:4b-instruct-2507-q4_K_M"

# Seuil de declenchement, en tokens lus au dernier appel. Bas expres :
# en production ce serait proche de la fenetre du modele.
SEUIL_TOKENS = 400

# Strategie appliquee au depassement : "tronquer", "compacter",
# ou None pour laisser grossir (comportement de 02_chat.py).
STRATEGIE = "compacter"

MESSAGE_SYSTEM = {
    "role": "system",
    "content": "Tu es un assistant concis. Reponds en francais, "
    "en 2 ou 3 phrases maximum.",
}


def appeler(messages):
    """Envoie l'historique au modele ; renvoie (reponse, tokens_lus)."""
    reponse = httpx.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "options": {"num_predict": 300},  # leçon de l'incident 04
        },
        timeout=120,
    )
    donnees = reponse.json()
    return donnees["message"]["content"], donnees.get("prompt_eval_count", 0)


def tronquer(messages, garder=4):
    """>>> EXERCICE — a ecrire par Anthony. Specification complete :

    Renvoie une NOUVELLE liste contenant :
      1. le message system (toujours messages[0] — jamais jete !) ;
      2. les `garder` derniers messages de la conversation (les plus
         recents), soit par defaut 4 messages = 2 echanges.

    Contraintes :
      - ne PAS modifier la liste recue (pas de .pop() dessus) ;
      - utiliser le slicing : messages[-garder:] donne les `garder`
        derniers elements ; [a] + b concatene une liste d'un element
        avec une liste b.
      - cas limite : si la conversation a moins de `garder` messages,
        messages[-garder:] les renvoie tous — rien de special a coder.

    Test de validation (S = system, u = user, a = assistant) :
      tronquer([S, u1, a1, u2, a2, u3, a3], garder=4)
      doit renvoyer [S, u2, a2, u3, a3]
      (les 4 derniers messages sont u2, a2, u3, a3 — et S est rajoute
      devant ; u1/a1, les plus vieux, sont oublies).
    """
    resultat = [messages[0]] + messages[-garder:]
    return resultat


def compacter(messages):
    """Remplace les vieux echanges par un resume ecrit par le modele.

    C'est un appel LLM DANS la mecanique du chat : le modele travaille
    pour sa propre memoire. On garde le system et on repart avec un seul
    message contenant le resume.
    """
    # Transcript texte de la conversation (sans le message system) :
    # une expression generatrice dans join() — compacte et lisible.
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in messages[1:])

    consigne = (
        "Resume la conversation suivante en 5 phrases maximum, en "
        "conservant imperativement les faits concrets (prenoms, lieux, "
        "chiffres, decisions). Reponds par le resume seul.\n\n" + transcript
    )
    resume, _ = appeler([{"role": "user", "content": consigne}])

    # Observabilite : sans voir le resume, impossible de diagnostiquer
    # une perte d'information (lecon du test du 19/07 : rappel echoue —
    # resume fautif ou modele fautif ? il faut la trace pour trancher).
    print(f"   [compaction : {len(messages) - 1} messages -> 1 resume]")
    print(f"   [resume : {resume}]")
    # Le resume va dans le message SYSTEM, pas dans un message user :
    # teste le 19/07, un resume en message user etait ignore par le
    # modele (reflexe "je ne stocke pas d'infos personnelles" malgre un
    # resume parfait). En system, c'est la voix qui fait autorite.
    return [
        {
            "role": "system",
            "content": MESSAGE_SYSTEM["content"]
            + " Memoire de la conversation en cours (utilise ces faits "
            + "pour repondre) : "
            + resume,
        },
    ]


messages = [MESSAGE_SYSTEM]
dernier_contexte = 0  # tokens lus au dernier appel

print(f"Chat avec gestion du contexte — strategie : {STRATEGIE}, "
      f"seuil : {SEUIL_TOKENS} tokens. /quit pour sortir.\n")

while True:
    saisie = input("toi> ").strip()
    if saisie == "/quit":
        break
    if not saisie:
        continue

    # AVANT d'ajouter le nouveau message : le contexte a-t-il deborde
    # au tour precedent ?
    if dernier_contexte > SEUIL_TOKENS:
        if STRATEGIE == "tronquer":
            avant = len(messages)
            messages = tronquer(messages)
            print(f"   [troncature : {avant} -> {len(messages)} messages]")
        elif STRATEGIE == "compacter":
            messages = compacter(messages)

    messages.append({"role": "user", "content": saisie})
    contenu, dernier_contexte = appeler(messages)
    messages.append({"role": "assistant", "content": contenu})

    print(f"\nqwen3> {contenu}\n")
    print(f"   [contexte lu : {dernier_contexte} tokens | "
          f"messages en memoire : {len(messages)}]\n")

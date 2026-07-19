"""Chat CLI avec historique de conversation.

LA lecon de ce script : le modele n'a AUCUNE memoire. Chaque appel HTTP
est independant et repart de zero. Ce qu'on appelle "la conversation",
c'est une liste de messages que NOUS gardons cote client, et que nous
renvoyons EN ENTIER a chaque tour. Le modele relit tout depuis le debut,
a chaque fois.

Consequence visible : le compteur de tokens du contexte (affiche apres
chaque reponse) grossit a chaque tour — on paye la relecture de tout
l'historique a chaque appel. C'est pour ca que la fenetre de contexte
finit toujours par deborder, et qu'il faudra tronquer ou resumer.
"""

import httpx

OLLAMA_URL = "http://192.168.1.57:11434"
MODEL = "qwen3:4b-instruct-2507-q4_K_M"

# L'historique complet. Le message "system" donne au modele son role :
# il est lu a chaque tour, comme tout le reste.
messages = [
    {
        "role": "system",
        "content": "Tu es un assistant concis. Reponds en francais, "
        "en 2 ou 3 phrases maximum.",
    },
]

print(f"Chat avec {MODEL} — tape /quit pour sortir.\n")

while True:
    saisie = input("toi> ").strip()
    if saisie == "/quit":
        break
    if not saisie:
        continue

    # 1. On ajoute le message utilisateur a l'historique...
    messages.append({"role": "user", "content": saisie})

    # 2. ...et on envoie TOUT l'historique, pas juste la derniere phrase.
    reponse = httpx.post(
        f"{OLLAMA_URL}/api/chat",
        json={"model": MODEL, "messages": messages, "stream": False},
        timeout=120,
    )
    donnees = reponse.json()
    contenu = donnees["message"]["content"]

    # 3. On ajoute AUSSI la reponse du modele a l'historique. Sans ca,
    #    au tour suivant il ne saurait plus ce qu'il a dit lui-meme.
    messages.append({"role": "assistant", "content": contenu})

    print(f"\nqwen3> {contenu}\n")

    # Metadonnees renvoyees par Ollama :
    #   prompt_eval_count = tokens LUS (system + tout l'historique)
    #   eval_count        = tokens GENERES (la reponse seule)
    # Regarde prompt_eval_count grossir tour apres tour.
    lus = donnees.get("prompt_eval_count", "?")
    generes = donnees.get("eval_count", "?")
    print(f"   [contexte lu : {lus} tokens | reponse : {generes} tokens]\n")

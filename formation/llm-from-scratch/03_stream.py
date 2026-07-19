"""Streaming : afficher la reponse au fil de la generation.

Un LLM genere sa reponse token par token, dans l'ordre, sans retour en
arriere. Avec "stream": false (scripts 01 et 02), Ollama attendait la fin
puis envoyait tout. Avec "stream": true, il envoie UNE LIGNE DE JSON PAR
MORCEAU genere, au fil de l'eau, sur la meme connexion HTTP.

C'est ce que fait toute interface de chat (ChatGPT, Claude...) : l'effet
"machine a ecrire" n'est pas cosmetique, c'est la realite du modele.

Nouveautes Python : json.loads (parser du JSON), with (fermer proprement
une ressource), "".join(liste) (recoller des morceaux de texte).
"""

import json

import httpx

OLLAMA_URL = "http://192.168.1.57:11434"
MODEL = "qwen3:4b-instruct-2507-q4_K_M"

messages = [
    {
        "role": "system",
        "content": "Tu es un assistant concis. Reponds en francais, "
        "en 2 ou 3 phrases maximum.",
    },
]

print(f"Chat (streaming) avec {MODEL} — tape /quit pour sortir.\n")

while True:
    saisie = input("toi> ").strip()
    if saisie == "/quit":
        break
    if not saisie:
        continue

    messages.append({"role": "user", "content": saisie})

    # httpx.stream ouvre la connexion et la laisse ouverte : on lit la
    # reponse ligne par ligne AU FUR ET A MESURE qu'Ollama l'ecrit.
    # Le "with" garantit que la connexion sera fermee a la fin du bloc.
    with httpx.stream(
        "POST",
        f"{OLLAMA_URL}/api/chat",
        json={"model": MODEL, "messages": messages, "stream": True},
        timeout=120,
    ) as reponse:
        print("\nqwen3> ", end="", flush=True)
        morceaux = []
        for ligne in reponse.iter_lines():
            if not ligne:
                continue
            # Chaque ligne est un petit document JSON independant :
            #   {"message": {"content": "Bon"}, "done": false}
            #   {"message": {"content": "jour"}, "done": false}
            #   ... puis une derniere ligne avec "done": true et les stats.
            chunk = json.loads(ligne)

            morceau = chunk["message"]["content"]
            # end="" : ne pas sauter de ligne ; flush=True : afficher
            # immediatement sans attendre que le tampon soit plein.
            print(morceau, end="", flush=True)
            morceaux.append(morceau)

            if chunk["done"]:
                # La derniere ligne contient les memes stats que le mode
                # non-streaming : prompt_eval_count, eval_count...
                #
                # >>> EXERCICE (a toi d'ecrire !) : afficher ici le
                # >>> compteur de tokens comme dans 02_chat.py.
                # >>> Indice : les stats sont dans `chunk`, et le format
                # >>> a reproduire est :
                # >>>   [contexte lu : N tokens | reponse : N tokens]
                lus = chunk.get("prompt_eval_count", "?")
                generes = chunk.get("eval_count", "?")
                print("\n")
                print(f"    [contexte lu : {lus} tokens | reponse : {generes} tokens]\n")
                break

        print("\n")

    # L'historique, lui, veut le texte COMPLET : on recolle les morceaux.
    contenu = "".join(morceaux)
    messages.append({"role": "assistant", "content": contenu})

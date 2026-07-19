"""Function calling a la main : donner au modele le pouvoir de demander.

LE concept a bien comprendre (question d'entretien classique !) :
le modele N'EXECUTE RIEN. Il ne fait toujours que generer du texte,
comme depuis 01_hello.py. Le mecanisme complet :

  1. On ANNONCE au modele un catalogue d'outils (des schemas JSON qui
     decrivent nom, utilite, parametres) — champ "tools" de la requete.
  2. Si le modele juge qu'un outil l'aiderait, il repond non pas du
     texte mais un "tool_call" : « appelle heure_actuelle() pour moi ».
     C'est une DEMANDE, en JSON.
  3. NOTRE code lit la demande, execute la vraie fonction Python, et
     renvoie le resultat dans la conversation (message role "tool").
  4. Le modele lit le resultat et redige sa reponse finale (ou demande
     un autre outil — d'ou la boucle).

Qui a le pouvoir ? Nous. Le modele propose, le code dispose. C'est la
que se joue toute la securite des agents (liste noire, validation
humaine... — architecture/securite.md du homelab).

Nouveautes Python : import de datetime, def a plusieurs fonctions,
dictionnaire de fonctions (dispatch), fonction(**args).
"""

from datetime import datetime

import httpx

OLLAMA_URL = "http://192.168.1.57:11434"
MODEL = "qwen3:4b-instruct-2507-q4_K_M"


# --------------------------------------------------------------------
# 1. Les outils : des fonctions Python parfaitement ordinaires.
# --------------------------------------------------------------------

def heure_actuelle():
    """L'exemple parfait : une info que le modele ne PEUT PAS savoir
    (ses connaissances sont figees a son entrainement)."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculer(expression):
    """Deuxieme classique : le calcul exact, la ou un LLM approxime.

    eval() execute du code arbitraire — DANGEREUX en general. Ici on
    filtre d'abord : uniquement chiffres et operateurs. C'est un avant-
    gout du sandboxing d'agents (le modele fournit l'argument, donc
    l'argument est une entree NON FIABLE, comme un champ de formulaire
    web).
    """
    autorises = set("0123456789+-*/(). ")
    if not set(expression) <= autorises:
        return "Erreur : seuls les chiffres et + - * / ( ) sont autorises"
    try:
        return str(eval(expression))
    except Exception as erreur:
        return f"Erreur de calcul : {erreur}"


def modeles_charges():
    """>>> EXERCICE — a ecrire par Anthony. Specification complete :

    But : dire quels modeles sont charges en VRAM sur jarvis-central
    (l'endpoint decouvert dans guides/methodologie-debug.md).

    A faire :
      1. GET sur f"{OLLAMA_URL}/api/ps" avec httpx.get(url, timeout=10),
         puis .json() sur la reponse.
      2. La reponse est un dict avec une cle "models" : une liste de
         dicts ayant chacun "name" (str) et "size_vram" (int, en octets).
      3. Si la liste est vide : renvoyer "Aucun modele charge."
      4. Sinon renvoyer une chaine, un modele par ligne, au format :
         "qwen3:4b-instruct-2507-q4_K_M — 3.0 Go de VRAM"
         (conversion octets -> Go : size_vram / 1024**3, arrondi a
         1 decimale avec round(x, 1)).

    Puis, pour le brancher (3 endroits, cherche les marqueurs [EXO]) :
      5. Ajouter son schema JSON dans TOOLS (modele : heure_actuelle,
         qui n'a pas non plus de parametres) — description soignee,
         c'est ELLE qui permet au modele de choisir le bon outil.
      6. L'ajouter au dictionnaire FONCTIONS.
      7. Tester avec : « Quels modeles tournent sur le serveur ? »
    """
    reponse = httpx.get(f"{OLLAMA_URL}/api/ps", timeout=10)
    donnees = reponse.json()
    models = donnees.get("models", [])
    if not models:
        return "Aucun modele charge."
    resultat = []
    for modele in models:
        nom = modele["name"]
        vram = round(modele["size_vram"] / 1024**3, 1)
        resultat.append(f"{nom} — {vram} Go de VRAM")
    return "\n".join(resultat)


# --------------------------------------------------------------------
# 2. Le catalogue annonce au modele : des schemas JSON. La description
#    est cruciale — c'est UNIQUEMENT sur elle (et le nom) que le modele
#    decide d'appeler ou non l'outil.
# --------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "heure_actuelle",
            "description": "Donne la date et l'heure actuelles. A utiliser "
            "pour toute question sur l'heure, la date ou le jour.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculer",
            "description": "Calcule exactement une expression arithmetique. "
            "A utiliser pour tout calcul plutot que de le faire de tete.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Expression avec + - * / ( ), "
                        "ex : '(1500 - 320) * 0.2'",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "modeles_charges",
            "description": "Liste les modeles actuellement charges en VRAM "
            "sur le serveur Ollama. A utiliser pour connaitre les informations sur les modeles charges.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    }
]

# Le "dispatch" : du nom (str, venant du modele) vers la fonction
# Python. C'est aussi une barriere de securite : un nom hors de ce
# dict ne sera jamais execute.
FONCTIONS = {
    "heure_actuelle": heure_actuelle,
    "calculer": calculer,
    "modeles_charges": modeles_charges,
}


def appeler(messages):
    """Appel au modele, catalogue d'outils inclus. Renvoie le message
    complet (pas juste le texte : il peut contenir des tool_calls)."""
    reponse = httpx.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": MODEL,
            "messages": messages,
            "tools": TOOLS,
            "stream": False,
            "options": {"num_predict": 800},
        },
        timeout=120,
    )
    return reponse.json()["message"]


messages = [
    {
        "role": "system",
        "content": "Tu es un assistant concis, en francais. Utilise les "
        "outils fournis quand ils sont pertinents.",
    },
]

print("Chat avec outils — /quit pour sortir.\n")

while True:
    saisie = input("toi> ").strip()
    if saisie == "/quit":
        break
    if not saisie:
        continue

    messages.append({"role": "user", "content": saisie})

    # Boucle de resolution : tant que le modele demande des outils,
    # on execute et on lui renvoie les resultats.
    while True:
        message = appeler(messages)
        messages.append(message)  # sa demande fait partie de l'historique !

        appels = message.get("tool_calls")
        if not appels:
            break  # pas de demande d'outil : c'est la reponse finale

        for appel in appels:
            nom = appel["function"]["name"]
            args = appel["function"]["arguments"]  # deja un dict (merci Ollama)
            print(f"   [le modele demande : {nom}({args})]")

            fonction = FONCTIONS.get(nom)
            if fonction is None:
                resultat = f"Outil inconnu : {nom}"
            else:
                resultat = fonction(**args)  # deballe le dict en arguments
            print(f"   [resultat execute par NOTRE code : {resultat}]")

            # Le resultat entre dans la conversation avec le role "tool".
            messages.append({"role": "tool", "content": str(resultat)})

    print(f"\nqwen3> {message['content']}\n")

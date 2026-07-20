"""Mini-boucle d'agent : quand les outils se mettent a AGIR.

La revelation de cette etape : la boucle d'agent, on l'a DEJA ecrite.
C'est celle de 06_outils.py, inchangee (comparez, elle est copiee telle
quelle plus bas). La definition honnete d'un agent :

    agent = un LLM + des outils + une boucle while

Ce qui change ici, ce n'est pas la mecanique, c'est la NATURE des
outils. Jusqu'ici ils lisaient des infos (heure, modeles charges).
Maintenant ils ecrivent sur le disque et executent des commandes :
l'agent agit sur le monde. Et des qu'on agit, la securite change de
categorie. Trois garde-fous, tous visibles dans ce fichier :

  1. SANDBOX : l'agent ne voit qu'un dossier dedie (workspace/).
     chemin_securise() bloque l'evasion type "../../secrets.txt"
     (attaque classique dite "path traversal"). Analogie homelab :
     un volume Docker — le conteneur ne voit que ce qu'on lui monte.
  2. VALIDATION HUMAINE : toute commande shell est montree et doit
     etre confirmee au clavier avant d'etre executee. C'est le prompt
     de permission de Claude Code, version artisanale.
  3. BOUCLE BORNEE : MAX_TOURS coupe un agent qui tourne en rond —
     le cousin de num_predict (incident 04), a l'echelle de l'agent.

Regle d'or (deja vue en 06, encore plus vraie ici) : tout ce qui vient
du modele — noms de fichiers, contenus, commandes — est une entree
NON FIABLE. Le modele propose, le code dispose.

Nouveautes Python : pathlib.Path (chemins objets), read_text /
write_text, subprocess.run, exceptions levees/attrapees (raise/except).
"""

import subprocess
from pathlib import Path

import httpx

OLLAMA_URL = "http://192.168.1.57:11434"
MODEL = "qwen3:4b-instruct-2507-q4_K_M"

# Le bac a sable : un sous-dossier a cote de ce script. resolve()
# transforme en chemin absolu canonique (indispensable pour comparer).
SANDBOX = (Path(__file__).parent / "workspace").resolve()
SANDBOX.mkdir(exist_ok=True)  # cree le dossier s'il n'existe pas

MAX_TOURS = 10  # borne de la boucle d'outils (garde-fou n. 3)


# --------------------------------------------------------------------
# 1. La garde de securite : tout chemin passe par ici.
# --------------------------------------------------------------------

def chemin_securise(nom):
    """Convertit un nom venant du MODELE en chemin verifie.

    (SANDBOX / nom) colle le nom au bout du sandbox, resolve()
    normalise (les ".." sont appliques), puis on VERIFIE que le
    resultat est bien reste dans le sandbox. Si le modele demande
    "../../06_outils.py", resolve() donne un chemin HORS sandbox
    -> refus. C'est la barriere anti path-traversal.
    """
    chemin = (SANDBOX / nom).resolve()
    if not chemin.is_relative_to(SANDBOX):
        # raise = lancer une erreur (comme throw en JS). Les outils
        # l'attrapent avec try/except et renvoient le texte au modele.
        raise ValueError(f"Refus : '{nom}' sort du sandbox")
    return chemin


# --------------------------------------------------------------------
# 2. Les outils. Deux en lecture (fournis), un en ecriture (exercice),
#    un en execution (fourni, avec validation humaine).
# --------------------------------------------------------------------

def lister_fichiers():
    """Lecture seule : le contenu du sandbox, un nom par ligne."""
    noms = [f.name for f in SANDBOX.iterdir()]
    if not noms:
        return "Le workspace est vide."
    return "\n".join(sorted(noms))


def lire_fichier(nom):
    """Lecture seule, mais avec DEUX reflexes :
    - chemin_securise : le nom vient du modele, on ne lui fait pas
      confiance ;
    - troncature a 2000 caracteres : un fichier enorme injecte tel
      quel exploserait le contexte (lecon du 05, cote agent)."""
    try:
        chemin = chemin_securise(nom)
        contenu = chemin.read_text(encoding="utf-8")
    except ValueError as erreur:
        return str(erreur)
    except FileNotFoundError:
        return f"Fichier introuvable : {nom}"
    if len(contenu) > 2000:
        return contenu[:2000] + f"\n[... tronque, {len(contenu)} caracteres au total]"
    return contenu


def ecrire_fichier(nom, contenu):
    """>>> EXERCICE — a ecrire par Anthony. Specification complete :

    But : creer (ou ecraser) un fichier DANS le sandbox avec le
    contenu fourni par le modele.

    A faire, dans l'ordre :
      1. Obtenir le chemin via chemin_securise(nom), dans un bloc
         try. Si ValueError est levee : return str(erreur)
         (modele exact : le try/except de lire_fichier ci-dessus,
         sans le FileNotFoundError qui ne concerne que la lecture).
      2. Ecrire avec : chemin.write_text(contenu, encoding="utf-8")
         (le miroir exact de read_text).
      3. return f"Ecrit : {nom} ({len(contenu)} caracteres)"
         — l'agent a besoin d'une confirmation TEXTE, car le modele
         ne voit que ce qu'on lui renvoie, jamais le disque.


    Puis brancher l'outil (2 endroits, cherche les marqueurs [EXO]) :
      4. Son schema JSON dans TOOLS — deux parametres string REQUIS :
         "nom" (description : le nom du fichier, ex 'notes.txt') et
         "contenu" (description : le texte complet a ecrire).
         Modele a imiter : le schema de lire_fichier.
      5. L'entree "ecrire_fichier" dans le dict FONCTIONS.

    Test final : « Cree un fichier haiku.txt contenant un haiku sur
    le homelab » puis « Relis-le moi » (deux outils enchaines !).
    """

    try:
        chemin = chemin_securise(nom)
    except ValueError as erreur:
        return str(erreur)
    
    try:
        chemin.write_text(contenu, encoding="utf-8")
    except Exception as erreur:
        return str(erreur)
    return f"Ecrit : {nom} ({len(contenu)} caracteres)"


def executer_commande(commande):
    """Le plus dangereux : execution de commande shell. D'ou le
    garde-fou n. 2 : montrer la commande et demander confirmation
    a L'HUMAIN avant de lancer quoi que ce soit."""
    print(f"\n   !!! Le modele veut executer : {commande}")
    accord = input("   Autoriser ? [o/N] ").strip().lower()
    if accord != "o":
        # Le refus est une INFO pour le modele : il doit savoir que
        # sa demande n'a pas ete executee, sinon il croit que si.
        return "Commande refusee par l'utilisateur."
    resultat = subprocess.run(
        commande,
        shell=True,          # passe par le shell (cmd.exe sur Windows)
        cwd=SANDBOX,         # execute DANS le sandbox
        capture_output=True, # recupere stdout/stderr au lieu d'afficher
        text=True,           # en str plutot qu'en octets
        timeout=30,          # garde-fou : pas de commande infinie
    )
    sortie = (resultat.stdout + resultat.stderr).strip()
    return sortie if sortie else "(commande terminee, aucune sortie)"


# --------------------------------------------------------------------
# 3. Le catalogue annonce au modele (memes schemas JSON qu'en 06).
# --------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lister_fichiers",
            "description": "Liste les fichiers presents dans le workspace. "
            "A utiliser pour savoir quels fichiers existent.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lire_fichier",
            "description": "Lit le contenu d'un fichier du workspace. "
            "A utiliser pour consulter un fichier existant.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nom": {
                        "type": "string",
                        "description": "Le nom du fichier, ex : 'notes.txt'",
                    }
                },
                "required": ["nom"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ecrire_fichier",
            "description": "Ecrit un fichier dans le workspace. "
            "A utiliser pour creer ou modifier un fichier.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nom": {
                        "type": "string",
                        "description": "Le nom du fichier, ex : 'notes.txt'",
                    },
                    "contenu": {
                        "type": "string",
                        "description": "Le texte complet a ecrire dans le fichier.",
                    },
                },
                "required": ["nom", "contenu"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "executer_commande",
            "description": "Execute une commande shell dans le workspace "
            "(soumise a validation humaine). A utiliser pour toute action "
            "qu'aucun autre outil ne couvre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "commande": {
                        "type": "string",
                        "description": "La commande shell, ex : 'dir'",
                    }
                },
                "required": ["commande"],
            },
        },
    },
]

FONCTIONS = {
    "lister_fichiers": lister_fichiers,
    "lire_fichier": lire_fichier,
    "ecrire_fichier": ecrire_fichier,
    "executer_commande": executer_commande,
}


# --------------------------------------------------------------------
# 4. La boucle d'agent — copiee de 06_outils.py, VOLONTAIREMENT :
#    c'est le point pedagogique. Seule nouveaute : la borne MAX_TOURS.
# --------------------------------------------------------------------

def appeler(messages):
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
        "content": "Tu es un agent qui travaille dans un dossier de "
        "fichiers (le workspace). Utilise les outils fournis pour agir, "
        "puis reponds en francais, de facon concise.",
    },
]

print(f"Mini-agent — sandbox : {SANDBOX}")
print("Il peut lister/lire/ecrire des fichiers et executer des commandes.")
print("/quit pour sortir.\n")

while True:
    saisie = input("toi> ").strip()
    if saisie == "/quit":
        break
    if not saisie:
        continue

    messages.append({"role": "user", "content": saisie})

    for tour in range(MAX_TOURS):
        message = appeler(messages)
        messages.append(message)

        appels = message.get("tool_calls")
        if not appels:
            break  # reponse finale

        for appel in appels:
            nom = appel["function"]["name"]
            args = appel["function"]["arguments"]
            print(f"   [demande : {nom}({args})]")

            fonction = FONCTIONS.get(nom)
            if fonction is None:
                resultat = f"Outil inconnu : {nom}"
            else:
                resultat = fonction(**args)
            print(f"   [resultat : {resultat}]")

            messages.append({"role": "tool", "content": str(resultat)})
    else:
        # Ce else appartient au FOR (nouveaute Python !) : il ne
        # s'execute que si la boucle va au bout SANS break — donc si
        # MAX_TOURS est atteint. L'agent tournait en rond, on coupe.
        print(f"   [stop : {MAX_TOURS} tours d'outils atteints]")

    print(f"\nqwen3> {message['content']}\n")

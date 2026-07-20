"""Structured output : du texte libre aux donnees FIABLES.

Le probleme : un LLM genere du texte libre, mais une application a
besoin de donnees structurees. Si Jarvis doit couper une VM, il faut
{"machine": "jarvis-core", "action": "stop"}, pas une jolie phrase.

Trois niveaux de solution, tous dans ce script :

  1. DEMANDER poliment du JSON dans le prompt -> fragile (demo A) :
     bavardage autour, clotures ```json, champs manquants.
  2. CONTRAINDRE la generation (demo B) : le champ "format" d'Ollama
     recoit un schema JSON, et le serveur MASQUE les tokens qui
     violeraient la syntaxe pendant la generation. Repensez au
     pipeline du 04 (probabilites -> filtres -> tirage) : c'est un
     filtre de plus, grammatical. On ne demande plus, on contraint.
  3. VALIDER quand meme (Pydantic) : syntaxe garantie != contenu
     valide (une RAM negative, une priorite inventee...). Pydantic
     lit les type hints de la classe et valide LES DONNEES a
     l'execution — la reponse a la question « Python est-il type
     comme JS ? » posee en debut de parcours. Et si la validation
     echoue : on renvoie l'erreur au modele et on reessaie (retry),
     comme l'agent 07 s'est corrige apres l'echec de `rm`.

Nouveautes Python : les CLASSES (la premiere du parcours !),
l'heritage (class Serveur(BaseModel)), les type hints exploites a
l'execution, int | None, list[str], raise.
"""

import json

import httpx
from pydantic import BaseModel, Field, ValidationError

OLLAMA_URL = "http://192.168.1.57:11434"
MODEL = "qwen3:4b-instruct-2507-q4_K_M"


# --------------------------------------------------------------------
# 1. Le contrat de donnees : une classe Pydantic.
#
# Une classe = un moule a objets (analogie JS directe : class de
# ES6). Ici on herite de BaseModel : notre classe recoit tous les
# super-pouvoirs de Pydantic (validation, parsing JSON, generation
# de schema). Chaque ligne "nom: type" declare un champ.
# --------------------------------------------------------------------

class Serveur(BaseModel):
    """Fiche d'identite d'une machine du homelab, extraite d'un texte."""

    nom: str
    role: str = Field(description="Fonction principale de la machine")
    # int | None = "un entier OU rien" : si le texte ne donne pas la
    # RAM, le modele doit mettre null plutot qu'inventer. = None en
    # fait un champ optionnel (valeur par defaut).
    ram_go: int | None = None
    # list[str] : une liste de chaines. Par defaut : liste vide.
    services: list[str] = []


TEXTES = [
    "jarvis-central, c'est le NUC qui fait tourner Ollama et "
    "Home Assistant. Il a 32 Go de RAM.",
    "La machine jarvis-core sert aux gros calculs IA grace a sa "
    "RTX 4090. Elle est en pause pendant la formation.",
]


def appeler(messages, format_schema=None):
    """Appel au modele. Si format_schema est fourni, Ollama contraint
    la generation a respecter ce schema JSON (decodage contraint)."""
    corps = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {"num_predict": 800},
    }
    if format_schema is not None:
        corps["format"] = format_schema
    reponse = httpx.post(f"{OLLAMA_URL}/api/chat", json=corps, timeout=120)
    return reponse.json()["message"]["content"]


# --------------------------------------------------------------------
# 2. Demo A — demander poliment. Regardez la sortie brute : est-elle
#    directement digerable par json.loads ? Pas toujours...
# --------------------------------------------------------------------

def demo_demander_poliment():
    print("=== Demo A : JSON demande poliment dans le prompt ===\n")
    contenu = appeler([
        {
            "role": "system",
            "content": "Reponds UNIQUEMENT avec un objet JSON contenant "
            "les cles : nom, role, ram_go, services. Rien d'autre.",
        },
        {"role": "user", "content": TEXTES[0]},
    ])
    print(f"Sortie brute :\n{contenu}\n")
    try:
        json.loads(contenu)
        print("-> json.loads : OK (cette fois... relancez plusieurs fois !)\n")
    except json.JSONDecodeError as erreur:
        print(f"-> json.loads PLANTE : {erreur}\n")


# --------------------------------------------------------------------
# 3. Demo B — contraindre. model_json_schema() genere le schema JSON
#    de la classe (le meme genre de schema que TOOLS en 06 !), et
#    Ollama interdit tout token qui en sortirait.
# --------------------------------------------------------------------

def demo_contraindre():
    print("=== Demo B : generation contrainte par le schema ===\n")
    print(f"Le schema envoye :\n{json.dumps(Serveur.model_json_schema(), indent=2)}\n")
    contenu = appeler(
        [
            {"role": "system", "content": "Extrais les informations du texte."},
            {"role": "user", "content": TEXTES[0]},
        ],
        format_schema=Serveur.model_json_schema(),
    )
    print(f"Sortie brute :\n{contenu}\n")
    # model_validate_json = json.loads + verification des types +
    # construction de l'objet, en un seul appel.
    serveur = Serveur.model_validate_json(contenu)
    print(f"-> Objet Python type : {serveur!r}")
    print(f"-> Acces direct aux champs : serveur.nom = {serveur.nom}, "
          f"serveur.ram_go = {serveur.ram_go}\n")


# --------------------------------------------------------------------
# 4. La piece maitresse : extraction avec validation et retry.
# --------------------------------------------------------------------

def extraire(texte, classe, max_essais=3, contraindre=True):
    """>>> EXERCICE — a ecrire par Anthony. Specification complete :

    But : extraire du texte un objet de la classe Pydantic donnee,
    en reessayant si le modele produit des donnees invalides.
    C'est LA brique standard de toute app LLM serieuse.

    Parametres :
      - texte : le texte libre a analyser (str)
      - classe : la classe Pydantic cible (ex : Serveur — oui, une
        classe se passe en argument comme n'importe quelle valeur,
        exactement comme une fonction en JS)
      - max_essais : nombre maximum de tentatives (int, defaut 3)
      - contraindre : si True, utiliser le decodage contraint ;
        si False, demander poliment (pour comparer les deux modes)

    A faire, dans l'ordre :
      1. Construire la liste messages :
         - system : "Extrais les informations du texte en JSON avec "
           "les cles : " + ", ".join(classe.model_fields) + ". "
           "Mets null si une information est absente du texte."
           (classe.model_fields est un dict des champs de la classe ;
           ", ".join(...) sur un dict joint ses CLES — donc ici les
           noms de champs.)
         - user : le texte.
      2. Boucle for essai in range(max_essais):
         a. contenu = appeler(messages, format_schema=...) — le
            schema classe.model_json_schema() si contraindre est
            True, sinon None.
         b. Dans un try : return classe.model_validate_json(contenu)
            (si la validation passe, la fonction SORT ici — le
            return coupe la boucle, pas besoin de break.)
         c. except ValidationError as erreur :
            - afficher f"   [essai {essai + 1} invalide : {erreur}]"
            - ajouter a messages le message assistant :
              {"role": "assistant", "content": contenu}
            - puis le message user :
              {"role": "user", "content": f"Ce JSON est invalide : "
               f"{erreur}. Corrige et renvoie UNIQUEMENT le JSON."}
            (meme logique que le refus renvoye au modele en 07 :
            l'erreur est une INFORMATION pour qu'il se corrige.)
      3. Apres la boucle (donc si aucun essai n'a reussi) :
         raise ValueError(f"Extraction impossible apres {max_essais} essais")
         — on LEVE une erreur plutot que de renvoyer None : le code
         appelant ne doit jamais croire qu'il a un objet valide.

    Test : lancer le script. La section 5 appelle extraire() sur les
    deux textes, en mode contraint puis en mode poli. Comparer :
    le mode poli declenche-t-il des retries ?
    """
    messages = [
        {
            "role": "system",
            "content": "Extrais les informations du texte en JSON avec "
            "les cles : " + ", ".join(classe.model_fields) + ". "
            "Mets null si une information est absente du texte.",
        },
        {"role": "user", "content": texte},
    ]
    for essai in range(max_essais):
        contenu = appeler(
            messages,
            format_schema=classe.model_json_schema() if contraindre else None,
        )
        try:
            return classe.model_validate_json(contenu)
        except ValidationError as erreur:
            print(f"   [essai {essai + 1} invalide : {erreur}]")
            messages.append({"role": "assistant", "content": contenu})
            messages.append(
                {
                    "role": "user",
                    "content": f"Ce JSON est invalide : {erreur}. "
                    f"Corrige et renvoie UNIQUEMENT le JSON.",
                }
            )
    raise ValueError(f"Extraction impossible apres {max_essais} essais")



# --------------------------------------------------------------------
# 5. Banc d'essai.
# --------------------------------------------------------------------

if __name__ == "__main__":
    demo_demander_poliment()
    demo_contraindre()

    print("=== Extraction complete (exercice) ===\n")
    for mode, contraindre in [("contraint", True), ("poli", False)]:
        print(f"--- Mode {mode} ---")
        for texte in TEXTES:
            print(f"Texte : {texte[:60]}...")
            try:
                serveur = extraire(texte, Serveur, contraindre=contraindre)
            except (ValueError, ValidationError) as erreur:
                print(f"  -> ECHEC : {erreur}\n")
                continue
            if serveur is None:
                print("  -> extraire() n'est pas encore implementee.\n")
                break
            print(f"  -> {serveur!r}\n")

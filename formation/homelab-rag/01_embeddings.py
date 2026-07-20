"""
01_embeddings.py — premier contact avec les embeddings.

Un embedding transforme un texte en VECTEUR : une liste de nombres qui
encode le sens du texte. Analogie RGB : "crimson" et "firebrick" sont
des chaines sans rapport, mais leurs coordonnees RGB (220,20,60) et
(178,34,34) sont voisines — la ressemblance est devenue calculable.
Meme idee ici, avec ~768 dimensions apprises par le modele.

On appelle /api/embed d'Ollama (modele nomic-embed-text) et on observe
la forme du resultat. Comparer deux vecteurs (similarite cosinus),
c'est pour 02_similarite.py.
"""

import httpx

URL = "http://192.168.1.57:11434/api/embed"
MODELE = "nomic-embed-text"


def embedder(texte: str) -> list[float]:
    """Renvoie le vecteur d'embedding d'un texte."""
    reponse = httpx.post(
        URL,
        json={"model": MODELE, "input": texte},
        timeout=30,
    )
    reponse.raise_for_status()
    # "embeddings" est une liste de vecteurs (un par texte envoye,
    # l'API accepte des lots) ; on n'envoie qu'un texte -> le premier.
    return reponse.json()["embeddings"][0]


# Trois textes de longueurs tres differentes, expres :
# le vecteur, lui, aura toujours la meme taille.
TEXTES = [
    "bonjour",
    "Quelle est la strategie de backup du NAS ?",
    "Sauvegarde du Synology",
    "Le serveur jarvis-central heberge Ollama, Home Assistant, Whisper, "
    "Piper et openWakeWord pour fournir un assistant vocal entierement "
    "local : detection du mot de reveil, transcription, reflexion, voix.",
]

if __name__ == "__main__":
    for texte in TEXTES:
        vecteur = embedder(texte)
        apercu = ", ".join(f"{v:.3f}" for v in vecteur[:5])
        print(f"{len(vecteur)} dims | [{apercu}, ...] | << {texte[:45]} >>")

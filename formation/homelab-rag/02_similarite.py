"""
02_similarite.py — mesurer la proximite de sens entre deux textes.

La similarite cosinus mesure l'ANGLE entre deux vecteurs :
  - meme direction  -> 1.0  (sens identique)
  - perpendiculaires -> 0.0 (sans rapport)
  - (opposes -> -1.0, rare en pratique avec les embeddings)

La formule :

    cos(v1, v2) = produit_scalaire(v1, v2) / (norme(v1) * norme(v2))

  - produit scalaire : somme des produits terme a terme
      v1[0]*v2[0] + v1[1]*v2[1] + ... + v1[767]*v2[767]
  - norme : racine carree de la somme des carres (Pythagore en 768D)
      sqrt(v[0]**2 + v[1]**2 + ... + v[767]**2)

Rappel du 01 : Ollama renvoie des vecteurs de norme 1. Le denominateur
vaut donc ~1.0 et cos ~= produit scalaire. On ecrit quand meme la
formule complete : elle marche pour n'importe quels vecteurs, pas
seulement les notres.

=== EXERCICE ===================================================
Completer similarite_cosinus() (et rien d'autre : le protocole de
test en bas du fichier est deja ecrit, avec les valeurs attendues).

Outils Python utiles :
  - math.sqrt(x)          racine carree
  - zip(v1, v2)           parcourt deux listes EN PARALLELE :
                          for a, b in zip([1, 2], [10, 20]) donne
                          (a=1, b=10) puis (a=2, b=20)
  - sum(...)              additionne ; accepte une expression
                          generatrice : sum(a * b for a, b in zip(v1, v2))
================================================================
"""

import math

import httpx

URL = "http://192.168.1.57:11434/api/embed"
MODELE = "nomic-embed-text"


# Copie du 01 plutot qu'un import : "import 01_embeddings" est
# impossible, un nom de module Python ne peut pas commencer par un
# chiffre. On extraira un module commun quand le pipeline deviendra
# serieux (04).
def embedder(texte: str) -> list[float]:
    """Renvoie le vecteur d'embedding d'un texte."""
    reponse = httpx.post(
        URL,
        json={"model": MODELE, "input": texte},
        timeout=30,
    )
    reponse.raise_for_status()
    return reponse.json()["embeddings"][0]


def similarite_cosinus(v1: list[float], v2: list[float]) -> float:
    """Renvoie la similarite cosinus entre deux vecteurs (entre -1 et 1)."""
    # 1. le produit scalaire de v1 et v2
    # 2. la norme de v1, la norme de v2
    # 3. renvoyer produit / (norme1 * norme2)
    
    # 1. le produit scalaire de v1 et v2
    produit = sum(a * b for a, b in zip(v1, v2))
    # 2. la norme de v1, la norme de v2
    norme1 = math.sqrt(sum(a * a for a in v1))
    norme2 = math.sqrt(sum(b * b for b in v2))
    # 3. renvoyer produit / (norme1 * norme2)
    return produit / (norme1 * norme2)
    


if __name__ == "__main__":
    PHRASES = [
        "Quelle est la strategie de backup du NAS ?",     # 0
        "Sauvegarde du Synology",                          # 1
        "La recette de la tarte aux pommes de mamie",      # 2
        "What is the backup strategy for the NAS?",        # 3
    ]
    vecteurs = [embedder(p) for p in PHRASES]

    # (indice_a, indice_b, valeur attendue a 0.01 pres)
    PAIRES = [
        (0, 0, 1.00),   # une phrase vs elle-meme : angle nul
        (0, 1, 0.66),   # backup NAS vs sauvegarde Synology
        (0, 2, 0.53),   # backup NAS vs tarte aux pommes
        (1, 2, 0.48),   # sauvegarde Synology vs tarte aux pommes
        (0, 3, 0.81),   # backup NAS vs sa traduction anglaise
    ]

    for a, b, attendu in PAIRES:
        score = similarite_cosinus(vecteurs[a], vecteurs[b])
        ecart = "OK" if abs(score - attendu) < 0.01 else f"ATTENDU {attendu}"
        print(f"{score:.4f} [{ecart:>4}]  << {PHRASES[a][:38]} >> vs << {PHRASES[b][:38]} >>")

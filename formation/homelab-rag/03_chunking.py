"""
03_chunking.py — decouper la doc du homelab en morceaux embeddables.

Un embedding = UN point pour tout le texte. Un fichier entier -> sens
dilue (le vecteur "moyenne" tout). Une ligne seule -> sens orphelin
(plus de contexte). Le juste milieu ici : la SECTION markdown (bloc
"## ..."), une idee par morceau — et on garde fichier + titre en
metadonnees pour pouvoir citer les sources.

Limite connue (dette v1 assumee) : une ligne "## ..." DANS un bloc de
code ``` serait prise pour un titre. On verra si ca nous mord quand on
evaluera le RAG — c'est le genre de bug que les evals revelent.

=== EXERCICE ===================================================
Completer decouper_en_sections(). Le pattern est nouveau : un
ACCUMULATEUR. On lit ligne par ligne en remplissant un panier ;
quand on croise un "## ", on scelle le panier en cours (une
section) et on en ouvre un nouveau. Piege classique : ne pas
oublier de sceller le DERNIER panier apres la boucle.

Spec precise :
  - entree  : texte (contenu du fichier), fichier (chemin relatif, str)
  - sortie  : liste de dicts {"fichier": ..., "titre": ..., "texte": ...}
  - decoupe : chaque ligne qui commence par "## " (exactement) ouvre
              une nouvelle section
  - titre   : la ligne sans son prefixe "## " -> ligne[3:].strip() ;
              tout ce qui precede le premier "## " a pour titre "(intro)"
  - texte   : les lignes de la section jointes par "\\n" (la ligne
              "## ..." incluse, elle aide l'embedding), puis .strip()
  - filtre  : une section dont le texte strippe est vide n'est pas
              ajoutee (ex. une intro vide)
================================================================
"""

from pathlib import Path

# La racine du repo homelab : deux crans au-dessus de ce script
# (homelab-rag/ -> formation/ -> racine). parent est l'equivalent
# pathlib de "..".
RACINE = Path(__file__).parent.parent.parent
DOSSIERS_EXCLUS = {".git", ".venv", "__pycache__", "formation"}


def lister_fichiers_md(racine: Path) -> list[Path]:
    """Tous les .md du repo, sauf les dossiers exclus (le corpus)."""
    fichiers = []
    # rglob = glob recursif ; chemin.parts = le chemin decoupe en
    # morceaux ("architecture", "nas.md") — pratique pour exclure.
    for chemin in racine.rglob("*.md"):
        if not any(partie in DOSSIERS_EXCLUS for partie in chemin.parts):
            fichiers.append(chemin)
    return sorted(fichiers)


def decouper_en_sections(texte: str, fichier: str) -> list[dict]:
    """Decoupe un contenu markdown en sections (une par bloc "## ...")."""
    sections = []          # les paniers scelles
    titre = "(intro)"      # titre du panier en cours
    lignes = []            # contenu du panier en cours
    for ligne in texte.splitlines():
        ...  # A COMPLETER : si la ligne commence par "## ", sceller
        ...  # le panier en cours (join + strip + filtre vide) puis en
        ...  # ouvrir un nouveau ; sinon, ajouter la ligne au panier.
    ...  # A COMPLETER : sceller le dernier panier.
    return sections


if __name__ == "__main__":
    fichiers = lister_fichiers_md(RACINE)
    # encoding="utf-8" obligatoire : sans lui, Windows lit en cp1252
    # et les accents de la doc deviennent du charabia.
    toutes = []
    for chemin in fichiers:
        texte = chemin.read_text(encoding="utf-8")
        relatif = str(chemin.relative_to(RACINE))
        toutes.extend(decouper_en_sections(texte, relatif))

    tailles = [len(s["texte"]) for s in toutes]
    print(f"fichiers  : {len(fichiers)}  (attendu 19)")
    print(f"sections  : {len(toutes)}  (attendu 132)")
    print(f"tailles   : min {min(tailles)} / max {max(tailles)} / "
          f"moyenne {sum(tailles) // len(tailles)}  "
          f"(attendu 114 / 7830 / 1018)")

    print("\nnas.md, attendu 6 sections :")
    for s in toutes:
        if s["fichier"] == str(Path("architecture/nas.md")):
            print(f"  - {s['titre']}  ({len(s['texte'])} car.)")

    print("\nApercu d'un chunk (le plus petit du corpus) :")
    petit = min(toutes, key=lambda s: len(s["texte"]))
    print(f"--- {petit['fichier']} / {petit['titre']} ---")
    print(petit["texte"])

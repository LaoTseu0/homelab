"""
rag_commun.py — la boite a outils partagee du pipeline RAG.

A partir du 04, les scripts importent d'ici au lieu de copier-coller :

    from rag_commun import embedder, similarite_cosinus, charger_corpus

C'est la "promotion en bibliotheque" du code valide dans 01/02/03.
(Rappel du pourquoi : "import 03_chunking" est impossible, un nom de
module ne peut pas commencer par un chiffre.)
"""

import math
from pathlib import Path

import httpx

# --- Configuration partagee -------------------------------------------

OLLAMA = "http://192.168.1.57:11434"
MODELE_EMBED = "nomic-embed-text"
MODELE_CHAT = "qwen3:4b-instruct-2507-q4_K_M"

RACINE = Path(__file__).parent.parent.parent        # la racine du repo
BASE = Path(__file__).parent / "index.db"           # l'index SQLite (04)
DOSSIERS_EXCLUS = {".git", ".venv", "__pycache__", "formation"}


# --- Valide dans 01 ---------------------------------------------------

def embedder(texte: str) -> list[float]:
    """Renvoie le vecteur d'embedding d'un texte (768 floats, norme 1)."""
    reponse = httpx.post(
        f"{OLLAMA}/api/embed",
        json={"model": MODELE_EMBED, "input": texte},
        timeout=30,
    )
    reponse.raise_for_status()
    return reponse.json()["embeddings"][0]


# --- Valide dans 02 (ecrit par Anthony) -------------------------------

def similarite_cosinus(v1: list[float], v2: list[float]) -> float:
    """Renvoie la similarite cosinus entre deux vecteurs (entre -1 et 1)."""
    produit = sum(a * b for a, b in zip(v1, v2))
    norme1 = math.sqrt(sum(a * a for a in v1))
    norme2 = math.sqrt(sum(b * b for b in v2))
    return produit / (norme1 * norme2)


# --- Valide dans 03 ---------------------------------------------------

def lister_fichiers_md(racine: Path = RACINE) -> list[Path]:
    """Tous les .md du repo, sauf les dossiers exclus (le corpus)."""
    fichiers = []
    for chemin in racine.rglob("*.md"):
        if not any(partie in DOSSIERS_EXCLUS for partie in chemin.parts):
            fichiers.append(chemin)
    return sorted(fichiers)


def decouper_en_sections(texte: str, fichier: str) -> list[dict]:
    """Decoupe un contenu markdown en sections (une par bloc "## ...")."""
    # === A FAIRE (etape 1 de l'exercice 04) ===========================
    # Quand ta fonction du 03 affiche les bonnes valeurs (19 fichiers,
    # 132 sections...), recopie son corps ici et supprime le raise.
    # Les scripts 04+ l'importeront d'ici.
    # ==================================================================
    raise NotImplementedError("recopie ici ta fonction validee du 03")


def charger_corpus() -> list[dict]:
    """Tout le corpus decoupe : liste de {"fichier", "titre", "texte"}."""
    sections = []
    for chemin in lister_fichiers_md():
        texte = chemin.read_text(encoding="utf-8")
        relatif = str(chemin.relative_to(RACINE))
        sections.extend(decouper_en_sections(texte, relatif))
    return sections

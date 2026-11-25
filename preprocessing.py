"""Nettoyage du texte avant vectorisation."""
from __future__ import annotations

import re
import unicodedata


def nettoyer_texte(texte: str) -> str:
    """Normalise une phrase : minuscules, sans accents, sans ponctuation.

    La ponctuation est remplacée par un espace (et non supprimée) afin que
    « au-revoir » et « au revoir » donnent la même chose.

    >>> nettoyer_texte("  Salut, ÇA va ?! ")
    'salut ca va'
    >>> nettoyer_texte("Au-revoir")
    'au revoir'
    """
    if not isinstance(texte, str):
        return ""
    texte = texte.lower()
    texte = "".join(
        c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn"
    )
    texte = re.sub(r"[^a-z0-9\s]", " ", texte)
    return re.sub(r"\s+", " ", texte).strip()

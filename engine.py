"""Moteur de réponse : TF-IDF + similarité cosinus + seuil de confiance.

Principe (recherche par similarité, sans entraînement supervisé) :

1. les questions du jeu de données sont nettoyées puis vectorisées (TF-IDF) ;
2. la phrase de l'utilisateur subit le même traitement ;
3. on calcule la similarité cosinus avec toutes les questions connues ;
4. si le meilleur score atteint le seuil, on renvoie la réponse associée,
   sinon on demande poliment de reformuler.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .preprocessing import nettoyer_texte

CHEMIN_DATASET = Path(__file__).resolve().parent.parent / "data" / "dataset.csv"
SEUIL_PAR_DEFAUT = 0.4
MESSAGE_INCOMPRIS = "Je n'ai pas bien compris, peux-tu reformuler ?"


@dataclass(frozen=True)
class Reponse:
    """Résultat d'une interrogation du moteur."""

    texte: str
    score: float
    comprise: bool
    question_proche: str | None = None
    categorie: str | None = None


class ChatEngine:
    """Agent conversationnel à base de TF-IDF et de similarité cosinus."""

    def __init__(
        self,
        dataframe: pd.DataFrame,
        seuil: float = SEUIL_PAR_DEFAUT,
        graine: int | None = None,
    ) -> None:
        manquantes = {"questions", "reponses"} - set(dataframe.columns)
        if manquantes:
            raise ValueError(f"Colonnes manquantes dans le dataset : {sorted(manquantes)}")
        if not 0.0 <= seuil <= 1.0:
            raise ValueError("Le seuil doit être compris entre 0 et 1.")

        self.seuil = seuil
        self._rng = random.Random(graine)
        self.df = dataframe.dropna(subset=["questions", "reponses"]).reset_index(drop=True)
        self.questions_propres = self.df["questions"].map(nettoyer_texte)

        # n-grammes de caractères : robustes aux fautes de frappe et aux
        # variantes (« salut » / « saluut », « ca va » / « ça va »).
        self.vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        self.matrice = self.vectorizer.fit_transform(self.questions_propres)

    @classmethod
    def depuis_csv(cls, chemin: str | Path = CHEMIN_DATASET, **kwargs) -> "ChatEngine":
        """Construit le moteur à partir d'un CSV (questions, reponses[, categorie])."""
        return cls(pd.read_csv(chemin, encoding="utf-8"), **kwargs)

    def scores(self, texte: str) -> np.ndarray:
        """Similarité cosinus entre `texte` et chaque question du dataset."""
        propre = nettoyer_texte(texte)
        if not propre:
            return np.zeros(len(self.df))
        return cosine_similarity(self.vectorizer.transform([propre]), self.matrice)[0]

    def repondre(self, texte: str, seuil: float | None = None) -> Reponse:
        """Renvoie la meilleure réponse, ou un message d'incompréhension."""
        seuil = self.seuil if seuil is None else seuil
        similarites = self.scores(texte)
        meilleur = float(similarites.max())

        if meilleur < seuil:
            return Reponse(MESSAGE_INCOMPRIS, meilleur, comprise=False)

        # Plusieurs lignes peuvent avoir la même question : on varie la réponse.
        candidats = np.flatnonzero(similarites >= meilleur - 1e-9)
        ligne = self.df.iloc[int(self._rng.choice(list(candidats)))]
        return Reponse(
            texte=str(ligne["reponses"]),
            score=meilleur,
            comprise=True,
            question_proche=str(ligne["questions"]),
            categorie=str(ligne["categorie"]) if "categorie" in self.df.columns else None,
        )

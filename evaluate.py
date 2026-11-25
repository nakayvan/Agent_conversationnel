"""Évalue le moteur sur data/eval.csv et balaye le seuil de confiance.

Usage : python scripts/evaluate.py [--figure docs/seuil.png]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from chatbot import ChatEngine  # noqa: E402

RACINE = Path(__file__).resolve().parent.parent


def evaluer(moteur: ChatEngine, jeu: pd.DataFrame, seuil: float) -> dict:
    """Métriques pour un seuil donné.

    - bien_repondu : phrase du domaine, comprise ET de la bonne catégorie
    - rejet_correct : phrase hors domaine correctement refusée
    """
    dans = jeu[jeu.attendu != "hors_domaine"]
    hors = jeu[jeu.attendu == "hors_domaine"]
    ok_dans = 0
    for texte, attendu in zip(dans.texte, dans.attendu):
        r = moteur.repondre(texte, seuil=seuil)
        ok_dans += int(r.comprise and r.categorie == attendu)
    ok_hors = sum(not moteur.repondre(t, seuil=seuil).comprise for t in hors.texte)
    return {
        "seuil": seuil,
        "bien_repondu": ok_dans / len(dans),
        "rejet_correct": ok_hors / len(hors),
        "exactitude": (ok_dans + ok_hors) / len(jeu),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--figure", type=Path, help="enregistre la courbe seuil/métriques")
    args = p.parse_args()

    moteur = ChatEngine.depuis_csv(graine=0)
    jeu = pd.read_csv(RACINE / "data" / "eval.csv")
    res = pd.DataFrame([evaluer(moteur, jeu, s) for s in np.round(np.arange(0.1, 0.95, 0.05), 2)])
    print(res.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    meilleur = res.loc[res.exactitude.idxmax()]
    print(f"\nMeilleure exactitude : {meilleur.exactitude:.2%} au seuil {meilleur.seuil:.2f}")

    if args.figure:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(res.seuil, res.bien_repondu, marker="o", label="Phrases du domaine bien traitées")
        ax.plot(res.seuil, res.rejet_correct, marker="s", label="Hors-sujet correctement rejetés")
        ax.plot(res.seuil, res.exactitude, marker="^", lw=2.5, color="black", label="Exactitude globale")
        ax.axvline(moteur.seuil, ls="--", color="grey")
        ax.set(xlabel="Seuil de similarité", ylabel="Proportion", ylim=(0, 1.02),
               title="Effet du seuil sur le comportement de l'agent")
        ax.grid(alpha=.3); ax.legend(loc="lower center", fontsize=8)
        fig.tight_layout(); args.figure.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.figure, dpi=180)
        print(f"Figure enregistrée : {args.figure}")


if __name__ == "__main__":
    main()

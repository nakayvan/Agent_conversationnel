"""Interface en ligne de commande : `python -m chatbot chat`."""
from __future__ import annotations

from .engine import ChatEngine

SORTIES = {"exit", "quit", "stop", "q", "quitter"}


def boucle_console(moteur: ChatEngine, debug: bool = False) -> None:
    print("Agent Conv — tape 'exit' pour quitter.\n")
    while True:
        try:
            texte = input("Vous : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBot : Au revoir !")
            return
        if not texte:
            continue
        if texte.lower() in SORTIES:
            print("Bot : Au revoir !")
            return
        r = moteur.repondre(texte)
        print(f"Bot : {r.texte}")
        if debug:
            print(f"      [score={r.score:.2f} | seuil={moteur.seuil:.2f} | proche={r.question_proche!r}]")

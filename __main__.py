"""Point d'entrée : python -m chatbot {chat|gui} [--seuil X] [--debug]"""
from __future__ import annotations

import argparse

from .engine import SEUIL_PAR_DEFAUT, ChatEngine


def main() -> None:
    parser = argparse.ArgumentParser(prog="chatbot", description="Agent conversationnel TF-IDF")
    parser.add_argument("mode", nargs="?", choices=["chat", "gui"], default="chat",
                        help="chat : console (défaut) | gui : interface Tkinter")
    parser.add_argument("--seuil", type=float, default=SEUIL_PAR_DEFAUT,
                        help=f"seuil de similarité entre 0 et 1 (défaut : {SEUIL_PAR_DEFAUT})")
    parser.add_argument("--dataset", help="chemin d'un CSV personnalisé (questions, reponses)")
    parser.add_argument("--debug", action="store_true", help="affiche le score de similarité")
    args = parser.parse_args()

    kwargs = {"seuil": args.seuil}
    moteur = ChatEngine.depuis_csv(args.dataset, **kwargs) if args.dataset else ChatEngine.depuis_csv(**kwargs)

    if args.mode == "gui":
        from .gui import lancer
        lancer(moteur)
    else:
        from .cli import boucle_console
        boucle_console(moteur, debug=args.debug)


if __name__ == "__main__":
    main()

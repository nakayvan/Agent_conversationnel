"""Interface graphique Tkinter avec saisie texte et mode vocal (optionnel).

Les dépendances vocales (SpeechRecognition, PyAudio, pyttsx3) sont facultatives :
si elles sont absentes, l'interface fonctionne en mode texte seul.
Les opérations lentes (écoute, synthèse vocale) tournent dans un thread pour ne
jamais figer la fenêtre.
"""
from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import scrolledtext

from .engine import ChatEngine

try:  # modules optionnels
    import speech_recognition as sr
except ImportError:  # pragma: no cover
    sr = None
try:
    import pyttsx3
except ImportError:  # pragma: no cover
    pyttsx3 = None


class Application(tk.Tk):
    def __init__(self, moteur: ChatEngine) -> None:
        super().__init__()
        self.moteur = moteur
        self.file: "queue.Queue[tuple[str, str]]" = queue.Queue()
        self.voix_active = tk.BooleanVar(value=pyttsx3 is not None)

        self.title("Agent Conv — Assistant TF-IDF")
        self.geometry("680x520")
        self.minsize(480, 360)
        self._construire()
        self.after(100, self._traiter_file)
        self._afficher("Bot", "Bonjour ! Écris-moi ou clique sur « Parler ».")

    # ---------- construction ----------
    def _construire(self) -> None:
        self.chat = scrolledtext.ScrolledText(self, state="disabled", wrap=tk.WORD, font=("Segoe UI", 11))
        self.chat.pack(padx=10, pady=(10, 4), fill=tk.BOTH, expand=True)
        self.chat.tag_config("Vous", foreground="#1b5e20")
        self.chat.tag_config("Bot", foreground="#0d47a1")
        self.chat.tag_config("Info", foreground="#757575")

        bas = tk.Frame(self)
        bas.pack(fill=tk.X, padx=10, pady=(0, 6))
        self.saisie = tk.Entry(bas, font=("Segoe UI", 11))
        self.saisie.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.saisie.bind("<Return>", lambda _e: self.envoyer())
        self.saisie.focus()
        tk.Button(bas, text="Envoyer", command=self.envoyer).pack(side=tk.LEFT, padx=(6, 0))
        self.btn_vocal = tk.Button(bas, text="Parler", command=self.ecouter,
                                   state=tk.NORMAL if sr else tk.DISABLED)
        self.btn_vocal.pack(side=tk.LEFT, padx=(6, 0))

        options = tk.Frame(self)
        options.pack(fill=tk.X, padx=10, pady=(0, 8))
        tk.Checkbutton(options, text="Lire les réponses à voix haute", variable=self.voix_active,
                       state=tk.NORMAL if pyttsx3 else tk.DISABLED).pack(side=tk.LEFT)

    # ---------- affichage ----------
    def _afficher(self, auteur: str, texte: str) -> None:
        self.chat.config(state="normal")
        self.chat.insert(tk.END, f"{auteur} : {texte}\n\n", auteur)
        self.chat.config(state="disabled")
        self.chat.see(tk.END)

    def _traiter_file(self) -> None:
        """Les threads déposent leurs messages ici ; seul le thread Tk les affiche."""
        try:
            while True:
                auteur, texte = self.file.get_nowait()
                self._afficher(auteur, texte)
                if auteur == "Vous (vocal)":
                    self._repondre(texte)
                if auteur == "Info":
                    self.btn_vocal.config(state=tk.NORMAL if sr else tk.DISABLED)
        except queue.Empty:
            pass
        self.after(100, self._traiter_file)

    # ---------- logique ----------
    def _repondre(self, question: str) -> None:
        reponse = self.moteur.repondre(question).texte
        self._afficher("Bot", reponse)
        self._parler(reponse)

    def envoyer(self) -> None:
        question = self.saisie.get().strip()
        if not question:
            return
        self.saisie.delete(0, tk.END)
        self._afficher("Vous", question)
        self._repondre(question)

    def _parler(self, texte: str) -> None:
        if not (pyttsx3 and self.voix_active.get()):
            return

        def lire() -> None:
            try:  # un moteur par thread : pyttsx3 n'est pas thread-safe
                moteur_voix = pyttsx3.init()
                moteur_voix.say(texte)
                moteur_voix.runAndWait()
            except Exception:  # noqa: BLE001 — la voix ne doit jamais faire planter l'appli
                pass

        threading.Thread(target=lire, daemon=True).start()

    def ecouter(self) -> None:
        self.btn_vocal.config(state=tk.DISABLED)
        self._afficher("Info", "Écoute en cours… parle maintenant.")

        def capter() -> None:
            reconnaisseur = sr.Recognizer()
            try:
                with sr.Microphone() as source:
                    reconnaisseur.adjust_for_ambient_noise(source, duration=0.4)
                    audio = reconnaisseur.listen(source, timeout=6, phrase_time_limit=10)
                texte = reconnaisseur.recognize_google(audio, language="fr-FR")
                self.file.put(("Vous (vocal)", texte))
            except sr.WaitTimeoutError:
                self.file.put(("Info", "Aucune voix détectée."))
            except sr.UnknownValueError:
                self.file.put(("Info", "Je n'ai pas compris, peux-tu répéter ?"))
            except sr.RequestError:
                self.file.put(("Info", "Service de reconnaissance vocale indisponible (connexion ?)."))
            except OSError:
                self.file.put(("Info", "Aucun microphone accessible."))
            finally:
                self.file.put(("Info", ""))

        threading.Thread(target=capter, daemon=True).start()


def lancer(moteur: ChatEngine | None = None) -> None:
    Application(moteur or ChatEngine.depuis_csv()).mainloop()

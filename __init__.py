"""Agent conversationnel TF-IDF (projet SIA 417 – Université de Douala)."""
from .engine import ChatEngine, Reponse
from .preprocessing import nettoyer_texte

__all__ = ["ChatEngine", "Reponse", "nettoyer_texte"]
__version__ = "1.0.0"

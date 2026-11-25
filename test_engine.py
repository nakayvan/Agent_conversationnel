import pytest

from chatbot import ChatEngine, nettoyer_texte
from chatbot.engine import MESSAGE_INCOMPRIS


@pytest.fixture(scope="module")
def moteur():
    return ChatEngine.depuis_csv(graine=42)


@pytest.mark.parametrize("brut, attendu", [
    ("  Salut, ÇA va ?! ", "salut ca va"),
    ("Au-revoir", "au revoir"),
    ("S'il te plaît", "s il te plait"),
    ("", ""),
])
def test_nettoyage(brut, attendu):
    assert nettoyer_texte(brut) == attendu


def test_nettoyage_entree_invalide():
    assert nettoyer_texte(None) == ""
    assert nettoyer_texte(float("nan")) == ""


def test_question_exacte(moteur):
    r = moteur.repondre("bonjour")
    assert r.comprise and r.score == pytest.approx(1.0)


def test_insensible_a_la_casse_et_aux_accents(moteur):
    assert moteur.repondre("ÇA VA ?").comprise


def test_variante_proche(moteur):
    assert moteur.repondre("au revoir").comprise      # « au-revoir » dans le dataset
    assert moteur.repondre("salu").comprise            # faute de frappe


def test_hors_sujet_refuse(moteur):
    r = moteur.repondre("quelle est la capitale du Cameroun ?")
    assert not r.comprise and r.texte == MESSAGE_INCOMPRIS


@pytest.mark.parametrize("texte", ["", "   ", "???", "!!!"])
def test_entrees_vides(moteur, texte):
    r = moteur.repondre(texte)
    assert not r.comprise and r.score == 0.0


def test_jamais_de_reponse_nan(moteur):
    for q in moteur.df["questions"]:
        assert moteur.repondre(q).texte.lower() != "nan"


def test_seuil_modifiable(moteur):
    assert moteur.repondre("ça roule bien aujourd hui", seuil=0.99).comprise is False
    assert moteur.repondre("ça roule bien aujourd hui", seuil=0.0).comprise is True


def test_seuil_invalide():
    with pytest.raises(ValueError):
        ChatEngine.depuis_csv(seuil=1.5)


def test_dataset_sans_colonne(tmp_path):
    import pandas as pd
    pd.DataFrame({"a": [1]}).to_csv(tmp_path / "x.csv", index=False)
    with pytest.raises(ValueError):
        ChatEngine.depuis_csv(tmp_path / "x.csv")


def test_reponses_variees_pour_questions_dupliquees():
    reponses = {ChatEngine.depuis_csv(graine=s).repondre("merci").texte for s in range(30)}
    assert len(reponses) >= 2

from __future__ import annotations

from kill_scam.asks import HOOK_IDS, extract_asks

LOOKALIKE = """From: Direction générale des Finances publiques <service@impots-gouv.fr>
Subject: Votre remboursement d'impôt

Votre remboursement est disponible. Cliquez ici pour le recevoir aujourd'hui:
https://impots-gouv.fr/connexion
"""

FAKE_CONFIRM = (
    "You already bought this for €199. Click to cancel the order if this was not you."
)


def test_ask_negation_does_not_treat_picnic_or_no_password_as_theft() -> None:
    picnic = extract_asks("The picnic is still at 12:00. No action needed.")
    assert picnic.kinds == ()
    library = extract_asks("We will not ask for your password. Bring your library card.")
    assert "code" not in library.kinds


def test_lookalike_tax_mail_names_hooks() -> None:
    report = extract_asks(LOOKALIKE)
    assert "click" in report.kinds
    assert "authority" in report.hooks
    assert "reward" in report.hooks
    assert "urgency" in report.hooks
    joined = " ".join(report.findings).lower()
    assert "persuasion hook" in joined
    assert "authority" in joined
    assert set(report.hooks).issubset(HOOK_IDS)


def test_fake_confirmation_hook() -> None:
    report = extract_asks(FAKE_CONFIRM)
    assert "fake_confirmation" in report.hooks
    assert any("fake confirmation" in item.lower() for item in report.findings)


def test_school_ham_does_not_invent_a_click_ask() -> None:
    report = extract_asks(
        "From: Lycée Jean Moulin <secretariat@lycee-jean-moulin.example>\n"
        "La réunion a lieu mardi. Pas de paiement en ligne."
    )
    assert "pay" not in report.kinds
    assert "click" not in report.kinds

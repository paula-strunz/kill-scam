from __future__ import annotations

from kill_scam.agent import classify_message, iter_checklist
from kill_scam.asks import extract_asks
from kill_scam.models import STEP_IDS, CheckResult, StepResult

LOOKALIKE = """From: Direction générale des Finances publiques <service@impots-gouv.fr>
Subject: Votre remboursement d'impôt

Votre remboursement est disponible. Cliquez ici pour le recevoir aujourd'hui:
https://impots-gouv.fr/connexion
"""

BANK_HAM = """From: La Banque Postale <ne-pas-repondre@labanquepostale.fr>
Subject: Votre relevé de février

Bonjour, votre relevé du mois est disponible dans votre espace habituel.
Aucune action n'est demandée. Nous ne vous demanderons jamais un mot de passe par email.
"""

SCHOOL_HAM = """From: Lycée Jean Moulin <secretariat@lycee-jean-moulin.example>
Subject: Réunion parents-profs

La réunion a lieu mardi à 18h au gymnase. Merci d'apporter le carnet de correspondance.
Pas de paiement en ligne.
"""

NESTED = """From: Chronopost <suivi@chronopost.fr>
Subject: Colis en attente

Votre colis est bloqué. Réglez 0,99 € de frais ici:
http://chronopost.fr.suivi-colis.test/paiement
"""


def test_ask_negation_does_not_treat_picnic_or_no_password_as_theft() -> None:
    picnic = extract_asks("The picnic is still at 12:00. No action needed.")
    assert picnic.kinds == ()
    library = extract_asks("We will not ask for your password. Bring your library card.")
    assert "code" not in library.kinds


def test_lookalike_impots_is_likely_scam_without_network() -> None:
    result = classify_message(LOOKALIKE, allow_search=False)
    assert result.verdict == "likely_scam"
    joined = " ".join(result.reasons).lower()
    assert "look" in joined or "not the official" in joined or "not official" in joined
    assert "persuasion hook" in joined or "authority" in joined or "reward" in joined


def test_nested_chronopost_link_is_likely_scam() -> None:
    result = classify_message(NESTED, allow_search=False)
    assert result.verdict == "likely_scam"
    assert any("link" in reason.lower() for reason in result.reasons)


def test_official_bank_and_school_ham_are_ok() -> None:
    bank = classify_message(BANK_HAM, allow_search=False)
    school = classify_message(SCHOOL_HAM, allow_search=False)
    assert bank.verdict == "ok"
    assert school.verdict == "ok"


def test_checklist_runs_when_google_oauth_missing(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
    result = classify_message(LOOKALIKE, allow_search=False)
    assert result.verdict == "likely_scam"
    assert [step.id for step in result.steps] == list(STEP_IDS)


def test_iter_checklist_emits_all_five_steps() -> None:
    events = list(iter_checklist(LOOKALIKE, allow_search=False))
    step_events = [event for event in events if isinstance(event, StepResult)]
    finals = [event for event in events if isinstance(event, CheckResult)]
    seen_done = [event.id for event in step_events if event.status in {"done", "skipped"}]
    assert seen_done == list(STEP_IDS)
    assert len(finals) == 1
    assert finals[0].verdict == "likely_scam"
    assert [step.id for step in finals[0].steps] == list(STEP_IDS)

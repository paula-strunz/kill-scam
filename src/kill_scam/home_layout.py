"""Home-screen choices that do not need Streamlit.

When Gmail is not configured, paste is the door family testers see first.
When Gmail is configured, Connect Gmail stays first.
"""

from __future__ import annotations

from dataclasses import dataclass

from kill_scam.evals import load_fixtures

# English scam already in evals/fixtures.json. Read from disk only.
SAMPLE_FIXTURE_ID = "scam-fake-bank"

SAFETY_CAPTION = (
    "It never sends mail. It never deletes mail. It never writes to your mailbox. "
    "It never opens a suspicious website."
)

GMAIL_OPTIONAL_NOTE = (
    "Connect Gmail is optional and isn’t set up yet. "
    "You do not need it to run the five checks."
)


@dataclass(frozen=True)
class HomeLayout:
    paste_primary: bool
    headline: str
    intro: str
    french_line: str


def home_layout(gmail_configured: bool) -> HomeLayout:
    """Pick the home copy from whether Connect Gmail can run."""
    if gmail_configured:
        return HomeLayout(
            paste_primary=False,
            headline="Connect Gmail. We look at recent mail. You see every check.",
            intro=(
                "Kill Scam reads recent inbox messages and walks through **five checks** "
                "you can see: what it wants, who it claims to be, the web addresses, "
                "known campaigns, then **Looks OK / Be careful / Likely a scam**."
            ),
            french_line="",
        )
    return HomeLayout(
        paste_primary=True,
        headline="Paste a suspicious message. You see every check.",
        intro=(
            "Paste an SMS, a WhatsApp text, or an email that worries you. "
            "Then press **Check this message**. Kill Scam walks through **five checks** "
            "you can see: what it wants, who it claims to be, the web addresses, "
            "known campaigns, then **Looks OK / Be careful / Likely a scam**."
        ),
        french_line=(
            "En français : collez le message suspect, puis appuyez sur Check. "
            "Cinq vérifications s'affichent. N'ouvrez aucun lien."
        ),
    )


def sample_fixture_message(fixture_id: str = SAMPLE_FIXTURE_ID) -> str:
    """Body of one local eval fixture. Reads the JSON file only — no network."""
    for example in load_fixtures():
        if example.id == fixture_id:
            text = example.message.strip()
            if not text:
                raise LookupError(f"Fixture {fixture_id} has an empty message.")
            return text
    raise LookupError(f"Fixture {fixture_id} is not in the offline sample file.")

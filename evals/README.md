# Offline golden fixtures

These files are practice messages for Kill Scam. They are made up. They are not from a real inbox, and they do not need OpenAI, Gmail, or Arize keys.

```text
evals/fixtures.json
        |
        v
local five-step checklist
        |
        v
missed scam?  false alarm?
        |
        v
later: same rows become an Arize dataset
```

## What is in the file

`fixtures.json` is the golden set: the answer key we already trust.

Each example has:

| Field | Meaning |
| --- | --- |
| `id` | Stable name, such as `scam-fr-trop-percu` |
| `category` | The pattern, such as a fake refund or a school note |
| `gold_label` | `scam` or `ham` (ham means a normal message) |
| `gold_verdict` | What the checklist should land on: `likely_scam` or `ok` |
| `notes` | Why this row is in the set |
| `message` | The fake email or text to score |

France-facing rows follow hooks from the product notes in `docs/PRD.md`:

- Authority: a DGFiP / impôts message that is not the real tax site
- Reward: a precise trop-perçu (a supposed tax overpayment) that asks for a bank RIB
- Parcel: a La Poste lookalike that asks for a small fee
- Ham: a school note and a mairie (town hall) note with no payment and no link

Every new web address uses a `.test` domain. Those domains are reserved for examples. Do not open them. The checker only reads the name of the site.

## How this becomes an Arize dataset later

Arize is the place where scored checks can be stored and compared. This file is already shaped for that upload. Nothing here calls Arize.

| Fixture field | Later Arize role |
| --- | --- |
| `message` | Model input (`input_field`) |
| `gold_label` | Expected class (`label_field`): `scam` or `ham` |
| `gold_verdict` | Expected checklist output (`output_field`): `ok`, `suspicious`, or `likely_scam` |
| `id`, `category`, `notes` | Extra columns so a row can be found again |
| `metrics` | `missed_scam` (a scam marked ok) and `false_alarm` (a normal message marked suspicious or likely_scam) |

The dataset name in the file is `kill-scam-v1-classification`. Uploading it is a later step. It needs your own Arize space. This folder does not contain keys, and the commands below do not ask for them.

## Run the checks offline

From the repository root, with Python 3.11+ and the project dependencies installed (`pip install -e ".[dev]"`):

```bash
pytest tests/test_eval_fixtures.py tests/test_evals_cli.py
python -m kill_scam.evals
```

`pytest` checks that the file is balanced, synthetic, and scored correctly by the local checklist.

`python -m kill_scam.evals` prints missed scams and false alarms. You can point it at the same file:

```bash
python -m kill_scam.evals --fixtures evals/fixtures.json
```

If the package is installed, `kill-scam-eval` is the same command.

Both commands use the built-in checklist. They do not call OpenAI, they do not connect to Gmail, and they do not send traces to Arize. A missing `OPENAI_API_KEY`, Google client, or `ARIZE_API_KEY` is expected and fine.

Exit code `0` means no missed scam. Exit code `1` means at least one scam was marked ok. A false alarm is printed in the report and does not change that exit code.

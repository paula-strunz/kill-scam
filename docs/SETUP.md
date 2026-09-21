# Kill Scam — OAuth + hosting setup

Do this **after** Gmail V0 ([PR #6](https://github.com/paula-strunz/kill-scam/pull/6)) is merged into `dev`. This file is a checklist, not a code change.

V0 is: **connect Gmail (read-only)**, scan recent mail, run the **five-step checklist**. The app **never sends** and **never deletes** mail.

Google will not verify a public app yet. V0 is **Paula + allowlisted family** on an OAuth consent screen in **testing mode**. Strangers on the internet cannot sign in.

```text
Google Cloud (testing mode)
        |
        v
Paula + family as test users
        |
        v
Hosted Kill Scam (Render, Fly, or Mac Mini)
        |
        v
Open URL → Connect Gmail → check one recent message
```

---

## 1. Google Cloud OAuth (testing mode)

You need a Google account (Paula’s). Work in [Google Cloud Console](https://console.cloud.google.com/). Menu names move around; look for **APIs & Services** → **OAuth consent screen** and **Credentials**.

### Create or select a project

1. Open Google Cloud Console.
2. Create a new project, or select an existing one. A sensible name is **Kill Scam**.

### Turn on the Gmail API

1. Go to **APIs & Services** → **Library**.
2. Search **Gmail API**.
3. Select it and click **Enable**.

### OAuth consent screen: External, testing

1. Go to **APIs & Services** → **OAuth consent screen** (sometimes shown as Google Auth platform).
2. User type: **External**.
3. Publishing status: **Testing** (do not publish to production).
4. App name: **Kill Scam**.
5. User support email: **Paula’s email**.
6. Developer contact email: the same address is fine.

### Scopes (read-only only)

Add **only**:

- `https://www.googleapis.com/auth/gmail.readonly`

If Google also requires **openid** / **email** / **profile** for the sign-in button, that is OK. Do **not** add anything that can send, delete, or change mail (`gmail.send`, `gmail.modify`, and similar).

### Test users (Paula + family)

While the app is in testing mode, **only listed emails can connect**.

1. On the consent screen, find **Test users**.
2. Add Paula’s Gmail.
3. Add each family Gmail you want to invite.
4. Save.

Anyone not on this list will be blocked. That is expected.

### Create an OAuth client ID (Web application)

1. Go to **APIs & Services** → **Credentials**.
2. **Create credentials** → **OAuth client ID**.
3. Application type: **Web application** (not Desktop, not iOS).
4. Name it something like **Kill Scam web**.

### Authorized redirect URIs

Google sends the person **back** to Kill Scam after they sign in. The address must match **exactly** (including `http` vs `https` and a trailing slash).

**After Gmail V0 (#6) — this is the intended setup:**

| Where you run the app | Redirect URI to add in Google Cloud | Same value in the app |
| --- | --- | --- |
| Laptop (Streamlit) | `http://localhost:8501` | Default if `GOOGLE_REDIRECT_URI` is blank |
| Laptop (trailing slash) | `http://localhost:8501/` | Add both; Google treats them as different |
| Hosted (Render) | `https://YOUR-APP.onrender.com` | Set `GOOGLE_REDIRECT_URI` to this exact URL |
| Hosted (Fly) | `https://YOUR-APP.fly.dev` | Set `GOOGLE_REDIRECT_URI` to this exact URL |

Add **both** the local URIs now. Add the hosted URI **once you know the public URL** (after the first deploy). Then paste that same hosted URL into the host’s `GOOGLE_REDIRECT_URI` setting.

**If you are reading this before #6 merges** (current `dev` in this repo): Gmail still uses a **Desktop** OAuth flow and `http://localhost` on a random port. `.env.example` only has `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`. After #6, the app expects a **Web** client, default redirect `http://localhost:8501`, and `GOOGLE_REDIRECT_URI` for hosting. Use the table above once #6 is on `dev`.

### Env vars (never commit)

Copy `.env.example` to `.env` on a laptop, or set the same names on the host dashboard. **Never put real keys in git.**

| Name | After #6? | What it is |
| --- | --- | --- |
| `GOOGLE_CLIENT_ID` | Yes | From the OAuth client you just created |
| `GOOGLE_CLIENT_SECRET` | Yes | From the same client. Treat like a password |
| `GOOGLE_REDIRECT_URI` | Yes (hosted) | Must match the authorized redirect URI. Laptop default is `http://localhost:8501` |
| `KILL_SCAM_HOSTED` | Yes (hosted) | Set to `1` on Render/Fly so Gmail tokens stay in the browser session, not on a shared disk |
| `OPENAI_API_KEY` | Optional | Not required for the five checks |
| `OPENAI_MODEL` | Optional | Defaults to `gpt-4o-mini` if you add a key later |
| `ARIZE_API_KEY` | Optional | Your Arize tracing key |
| `ARIZE_SPACE_ID` | Optional | Your Arize space. Project name in the app is always `kill-scam` |

There is **no session secret** in `.env.example` today. If a later change adds one, set it on the host the same way and never commit it.

On current `dev` (before #6): only `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` exist. `GOOGLE_REDIRECT_URI` and `KILL_SCAM_HOSTED` arrive with #6.

### “Google hasn’t verified this app”

Testers will usually see a screen that says **Google hasn’t verified this app**. That is **expected** in testing mode.

They can continue with **Advanced** → **Go to Kill Scam (unsafe)**. It is Paula’s app, not a random site. Do not invite the whole internet.

```text
Tester clicks Connect Gmail
        |
        v
Google warning: app not verified   ← expected
        |
        v
Advanced → Go to Kill Scam
        |
        v
Allow read-only Gmail
```

---

## 2. Host so it runs with the laptop closed

Family should open a website, not run Python on Paula’s laptop.

**On this `dev` branch:** there is not yet a `Dockerfile`, `render.yaml`, or `fly.toml`. Those files land with **Gmail V0 PR #6**. Do the deploy steps below after #6 is merged (or from that PR’s branch if you are only practising).

Prefer **Render**. Fly is a short alternative. A **Mac Mini** at home is another option if you would rather not use Render — see **Option: Mac Mini instead of Render** below. That Mini path does **not** skip the Google OAuth checklist in section 1.

```text
GitHub `dev` (after #6)
        |
        v
Render (or Fly) runs the Docker image
        |
        v
https://YOUR-APP.onrender.com stays up
        |
        v
Laptop can be closed
```

### Primary: Render (minimal)

1. Wait until #6 is on `dev` so `Dockerfile` and `render.yaml` exist.
2. Sign in at [render.com](https://render.com/) with GitHub.
3. **New** → **Web Service** → this `kill-scam` repo, branch `dev` (or `main` after you promote).
4. Runtime: **Docker** (the `render.yaml` in #6 already says this).
5. In **Environment**, set at least:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URI` — leave a placeholder until you know the public URL, then set it
   - `KILL_SCAM_HOSTED` = `1`
   - Optional: `OPENAI_API_KEY`, `ARIZE_API_KEY`, `ARIZE_SPACE_ID`
6. Deploy. Copy the public URL (looks like `https://kill-scam-xxxx.onrender.com`).
7. Put that **exact** URL in:
   - Google Cloud → OAuth client → **Authorized redirect URIs**
   - Render → `GOOGLE_REDIRECT_URI`
8. Redeploy or restart if you changed env vars after the first deploy.

### Fly (short note)

`fly.toml` also lands with #6. From a machine with the [Fly CLI](https://fly.io/docs/flyctl/install/):

```bash
fly launch --no-deploy
fly secrets set GOOGLE_CLIENT_ID=... GOOGLE_CLIENT_SECRET=... GOOGLE_REDIRECT_URI=https://YOUR-APP.fly.dev KILL_SCAM_HOSTED=1
# optional:
# fly secrets set ARIZE_API_KEY=... ARIZE_SPACE_ID=... OPENAI_API_KEY=...
fly deploy
```

Then add `https://YOUR-APP.fly.dev` (or your custom domain) as an authorized redirect URI, matching `GOOGLE_REDIRECT_URI`.

### After deploy

1. Open the public URL.
2. **Connect Gmail** as a test user (Paula or an invited family address).
3. Check **one recent message**.
4. If Arize keys are set, open your Arize space and confirm a `kill-scam` trace appeared.

### Option: Mac Mini instead of Render

You can run Kill Scam on a Mac Mini that stays on at home, instead of Render. Family then open a website. This is an **alternative host**, not a replacement for the OAuth steps in section 1.

**The Mini must stay awake.** If it sleeps, the site stops.

1. Open **System Settings** (Apple menu).
2. Open **Energy** (on some Macs this is still called **Energy Saver**).
3. Turn on **Prevent automatic sleeping when the display is off**.
4. Leave the Mini plugged in.

**Install and run on a fixed port (8501).** You need Python 3.11 or newer, same as a laptop.

```bash
git clone https://github.com/paula-strunz/kill-scam.git
cd kill-scam
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
streamlit run src/kill_scam/app.py --server.port 8501
```

Leave that Terminal window running. On the Mini, open `http://localhost:8501`.

**Paste-check works without Google OAuth.** **Check something else** (paste SMS, WhatsApp, or email) works with no secrets. **Connect Gmail** still needs the OAuth client and env vars from section 1 — do that later when you are ready. When you do, put the public URL (the tunnel URL below, if you use one) in **Authorized redirect URIs** and `GOOGLE_REDIRECT_URI`, same idea as Render.

**Family outside home Wi‑Fi need a public tunnel.** Render already gives you a public URL. A Mini on home Wi‑Fi does not. Set up a tunnel **once** (Cloudflare Tunnel or Tailscale Funnel) so relatives not on your home network get a URL that works from anywhere.

```text
Mac Mini stays awake
        |
        v
Streamlit on port 8501
        |
        +--> at home: http://localhost:8501
        |
        +--> outside home Wi‑Fi: Cloudflare Tunnel or Tailscale Funnel (once)
                    |
                    v
              public URL for family
```

Render / Fly steps above stay valid. Use this Mini option only if you prefer a computer you already own.

---

## 3. Verify

- [ ] Connect Gmail works for a test user (Paula or invited family).
- [ ] A lookalike / suspicious mail gets **Likely a scam** or **Be careful**, with the five steps visible.
- [ ] A normal mail (school, newsletter, real bank you already trust) is **not** called a scam.
- [ ] The app never offers to send or delete mail, and Gmail still looks unchanged after a check.

---

## Out of scope

- Merging [PR #6](https://github.com/paula-strunz/kill-scam/pull/6) (needs a human glance; this docs PR does not merge it).
- Google **public** verification so anyone on the internet can connect.
- SMS, auto-delete, or writing to the mailbox.

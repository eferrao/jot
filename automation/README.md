# Daily priority email check-in

Emails each configured address every morning asking for their #1 priority,
then checks in every 3 hours. Each address gets its own list, kept only in
its own email thread — the inbox *is* the authentication, so there's no login
and no web page. Runs entirely on GitHub Actions cron (no server).

## How it works

- A **dedicated Gmail inbox** sends the prompts (SMTP) and receives replies.
- Each hourly run **polls that inbox over IMAP**, reads new replies, and
  updates state. So it's two-way without a webhook — your reply is processed
  on the next scheduled run, not instantly.
- Per-address lists persist in `automation/data/state.json`, which the
  workflow commits back after each change.

| Time (ET) | What happens |
|-----------|--------------|
| 7:00 am   | "What's your #1 priority for today?" |
| 10am, 1pm, 4pm, 7pm, 10pm | Asks if your #1 is done; reply `DONE` to close it out. |

The job actually fires hourly; `automation/email_checkin.py` decides whether
the current Eastern hour is a send slot (no-op otherwise) and reads replies
every run. This keeps timing right across EST/EDT, since GitHub cron is UTC
with no daylight-saving awareness.

## One-time setup

### 1. Create the dedicated Gmail inbox
Make a new Google account just for this (e.g. `yourname.checkins@gmail.com`)
so it's isolated from your personal mail.

### 2. Turn on 2-Step Verification & make an App Password
App Passwords require 2FA on the account.
1. Google Account → **Security** → enable **2-Step Verification**.
2. Then **Security → App passwords** (<https://myaccount.google.com/apppasswords>),
   create one named "jot check-ins", and copy the 16-character password.

### 3. Add GitHub repository secrets
**Settings → Secrets and variables → Actions → New repository secret**:

| Secret name | Value |
|-------------|-------|
| `GMAIL_ADDRESS` | the dedicated inbox, e.g. `yourname.checkins@gmail.com` |
| `GMAIL_APP_PASSWORD` | the 16-char App Password (no spaces) |
| `CONVERSATION_EMAILS` | comma-separated addresses to converse with, e.g. `you@gmail.com, teammate@work.com` |

### 4. Test it
- **Manually:** Actions → **Daily priority email check-in** → **Run workflow**
  → set *force* to `morning` → Run. Check the configured inboxes.
- **Locally (no send):** `python3 automation/email_checkin.py --dry-run --force morning`

## Important notes
- **Scheduled workflows only run from the repo's default branch.** This must
  be merged to `main` before the hourly cron fires. You can still test from any
  branch via **Run workflow** in the Actions tab.
- **Privacy:** `state.json` stores the configured email addresses and their
  todos in the repo. **Keep this repository private.**
- GitHub-scheduled runs can be delayed a few minutes under load, and pause
  after ~60 days of repo inactivity (any commit re-enables them).
- "Done" detection is keyword-based (done/yes/finished/all set, etc.).
- Reply parsing strips the quoted original message and a leading "my priority
  is…" phrase, but it's heuristic — unusual formatting may need a tweak.

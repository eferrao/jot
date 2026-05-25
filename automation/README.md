# Daily priority SMS check-in

Texts you each morning asking for your #1 priority, then checks in every 3
hours. Runs on GitHub Actions cron (no server, no machine of yours needs to
be on). Your replies are read back from Twilio's message log on the next
scheduled run — so it's two-way, just not instant.

## Schedule (US Eastern, DST-aware)

| Time (ET) | What happens |
|-----------|--------------|
| 7:00 am   | "Good morning! What's your #1 priority for today?" |
| 10am, 1pm, 4pm, 7pm, 10pm | Reads your latest reply; asks if your #1 is done (or cheers you on if you said it's finished). |

The workflow actually fires hourly; `automation/sms_checkin.py` decides
whether the current Eastern hour is a send slot and is a no-op otherwise.
This keeps timing correct across EST/EDT, since GitHub cron runs in UTC with
no daylight-saving awareness.

## One-time setup

### 1. Create a Twilio account & get a number
1. Sign up at <https://www.twilio.com/try-twilio> and verify your email + phone.
2. In the Twilio Console, go to **Phone Numbers → Manage → Buy a number** and
   buy an SMS-capable number (~$1–2/mo; the free trial includes credit).
3. **Trial-account note:** a trial account can only text numbers you've
   *verified*. Add `+12016389292` under **Phone Numbers → Verified Caller IDs**,
   or upgrade the account to remove the restriction.

### 2. Find your credentials
On the Twilio Console home page, copy:
- **Account SID** (starts with `AC…`)
- **Auth Token** (click to reveal)
- Your purchased **Twilio phone number** in E.164 form, e.g. `+15551234567`

### 3. Add them as GitHub repository secrets
In this repo: **Settings → Secrets and variables → Actions → New repository
secret**. Add all four:

| Secret name | Value |
|-------------|-------|
| `TWILIO_ACCOUNT_SID` | your `AC…` SID |
| `TWILIO_AUTH_TOKEN`  | your auth token |
| `TWILIO_FROM_NUMBER` | your Twilio number, e.g. `+15551234567` |
| `MY_PHONE_NUMBER`    | `+12016389292` |

Keeping the destination number in a secret avoids committing a personal phone
number into the repo.

### 4. Test it
- **Manually:** Actions tab → **Daily priority SMS check-in** → **Run
  workflow** → set *force* to `morning` or `checkin` → Run. You should get a
  text within a minute.
- **Locally (no send):** `python3 automation/sms_checkin.py --dry-run --force morning`

That's it — once the secrets are set, the hourly cron takes over automatically.

## Notes & limits
- GitHub-scheduled runs can be delayed several minutes under load, and may be
  paused on repos with no activity for 60+ days. A duplicate-guard skips a
  second send within the same hour.
- "Done" detection is keyword-based (done/yes/finished/✅, etc.) — good enough
  for a nudge, not exact.
- Cost is minimal: a few SMS/day plus the number rental. GitHub Actions
  minutes for these tiny jobs are within the free tier for most accounts.

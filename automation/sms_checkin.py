#!/usr/bin/env python3
"""Daily priority SMS check-in via Twilio, driven by GitHub Actions cron.

The morning run asks for the day's #1 priority. Later runs poll Twilio's
inbound message log to learn the priority (and whether you've said it's done)
and send a check-in accordingly. No webhook/server needed: replies are read
from Twilio's REST API on the next scheduled run.

Required environment variables:
  TWILIO_ACCOUNT_SID   Twilio account SID (starts with "AC")
  TWILIO_AUTH_TOKEN    Twilio auth token
  TWILIO_FROM_NUMBER   Your Twilio phone number, E.164 (e.g. +15551234567)
  MY_PHONE_NUMBER      Where to text you, E.164 (e.g. +12016389292)
"""

import argparse
import base64
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
API_ROOT = "https://api.twilio.com/2010-04-01"

MORNING_HOUR = 7            # ET hour to ask for the day's priority
CHECKIN_HOURS = {10, 13, 16, 19, 22}  # ET hours to check in (every 3h after 7)

DONE_WORDS = {"done", "yes", "yep", "yeah", "finished", "complete",
              "completed", "did it", "nailed it", "✅", "✔️"}


def _need(name):
    val = os.environ.get(name)
    if not val:
        sys.exit(f"Missing required environment variable: {name}")
    return val


def _auth_header(sid, token):
    raw = f"{sid}:{token}".encode()
    return "Basic " + base64.b64encode(raw).decode()


def twilio_request(method, path, sid, token, data=None):
    url = f"{API_ROOT}/Accounts/{sid}/{path}"
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", _auth_header(sid, token))
    if body:
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def send_sms(cfg, body, dry_run=False):
    print(f"SEND -> {cfg['to']}: {body}")
    if dry_run:
        return
    twilio_request(
        "POST", "Messages.json", cfg["sid"], cfg["token"],
        data={"From": cfg["from"], "To": cfg["to"], "Body": body},
    )


def list_recent_messages(cfg, page_size=50):
    """Return recent messages between the Twilio number and the user."""
    qs = urllib.parse.urlencode({"PageSize": page_size})
    payload = twilio_request(
        "GET", f"Messages.json?{qs}", cfg["sid"], cfg["token"]
    )
    return payload.get("messages", [])


def parse_twilio_date(raw):
    # Twilio returns RFC 2822, e.g. "Mon, 25 May 2026 11:00:00 +0000"
    from email.utils import parsedate_to_datetime
    try:
        return parsedate_to_datetime(raw).astimezone(ET)
    except (TypeError, ValueError):
        return None


def todays_inbound(messages, cfg, now):
    """User's inbound messages received today (ET), oldest first."""
    today = now.date()
    out = []
    for m in messages:
        if m.get("direction") != "inbound":
            continue
        if m.get("from") != cfg["to"]:
            continue
        sent = parse_twilio_date(m.get("date_sent"))
        if sent and sent.date() == today:
            out.append((sent, (m.get("body") or "").strip()))
    out.sort(key=lambda x: x[0])
    return out


def already_acted_this_hour(messages, cfg, now):
    """True if we already sent the user an outbound text this ET hour."""
    for m in messages:
        if m.get("direction", "").startswith("outbound") and m.get("to") == cfg["to"]:
            sent = parse_twilio_date(m.get("date_sent"))
            if sent and sent.date() == now.date() and sent.hour == now.hour:
                return True
    return False


def looks_done(text):
    low = text.lower()
    return any(w in low for w in DONE_WORDS)


def run(cfg, now, dry_run=False, force=None):
    hour = now.hour
    mode = force or (
        "morning" if hour == MORNING_HOUR
        else "checkin" if hour in CHECKIN_HOURS
        else None
    )
    if mode is None:
        print(f"Nothing scheduled for {now:%H:%M} ET. Exiting.")
        return

    messages = [] if dry_run else list_recent_messages(cfg)

    if not dry_run and already_acted_this_hour(messages, cfg, now):
        print("Already texted this hour; skipping to avoid duplicates.")
        return

    if mode == "morning":
        send_sms(cfg, "Good morning! What's your #1 priority for today?", dry_run)
        return

    # check-in
    inbound = [] if dry_run else todays_inbound(messages, cfg, now)
    if not inbound:
        send_sms(cfg, "Haven't heard your #1 priority yet today — what is it?", dry_run)
        return

    priority = inbound[0][1]
    latest = inbound[-1][1]

    if len(inbound) > 1 and looks_done(latest):
        send_sms(cfg, f"Nice work finishing \"{priority}\"! Anything else on deck?", dry_run)
    else:
        send_sms(cfg, f"Check-in: is your #1 (\"{priority}\") done yet?", dry_run)


def main():
    ap = argparse.ArgumentParser(description="Daily priority SMS check-in.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print actions without calling Twilio or requiring creds.")
    ap.add_argument("--force", choices=["morning", "checkin"],
                    help="Force a mode regardless of the current hour (for testing).")
    args = ap.parse_args()

    now = datetime.now(ET)

    if args.dry_run:
        cfg = {"sid": "AC_dry", "token": "x",
               "from": "+15555550000", "to": "+12016389292"}
    else:
        cfg = {
            "sid": _need("TWILIO_ACCOUNT_SID"),
            "token": _need("TWILIO_AUTH_TOKEN"),
            "from": _need("TWILIO_FROM_NUMBER"),
            "to": _need("MY_PHONE_NUMBER"),
        }

    run(cfg, now, dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    main()

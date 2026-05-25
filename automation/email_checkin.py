#!/usr/bin/env python3
"""Email-based daily priority check-in via a dedicated Gmail inbox.

Driven by GitHub Actions cron. Serverless and two-way without a webhook:
each run polls the inbox over IMAP to read replies, updates per-email state,
and sends prompts/check-ins over SMTP. The inbox itself is the authentication
-- a person's list is only ever emailed to, and updated from, their address.

Per-email lists persist in automation/data/state.json (committed by the
workflow).

Required environment variables:
  GMAIL_ADDRESS        the dedicated inbox, e.g. jot.checkins@gmail.com
  GMAIL_APP_PASSWORD   a Google App Password (requires 2FA on the account)
  CONVERSATION_EMAILS  comma-separated addresses to converse with
"""

import argparse
import email
import imaplib
import json
import os
import re
import smtplib
import ssl
import sys
from datetime import datetime
from email.message import EmailMessage
from email.utils import parseaddr
from pathlib import Path
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
STATE_PATH = Path(__file__).resolve().parent / "data" / "state.json"

MORNING_HOUR = 7
CHECKIN_HOURS = [10, 13, 16, 19, 22]

NEGATION_RE = re.compile(
    r"\b(not|isn'?t|haven'?t|hasn'?t|won'?t|can'?t|nope|nah|still|"
    r"in progress|wip|almost|not yet)\b", re.I)
DONE_RE = re.compile(
    r"\b(done|finished|complete|completed|did it|nailed it|all set|"
    r"yes|yep|yeah|yup)\b", re.I)


def looks_done(text):
    """True if a reply says the task is finished (negations win)."""
    if NEGATION_RE.search(text):
        return False
    return bool(DONE_RE.search(text))

SUBJECT = "Your #1 priority for today"

# Strip a quoted reply tail (the original message Gmail appends below a reply).
QUOTE_MARKERS = [
    re.compile(r"^On .+wrote:\s*$"),
    re.compile(r"^-+\s*Original Message\s*-+", re.I),
    re.compile(r"^_{5,}\s*$"),
    re.compile(r"^From:\s", re.I),
    re.compile(r"^Sent from my ", re.I),
]
PRIORITY_PREFIX = re.compile(
    r"^\s*(?:my\s+)?(?:#?1|number\s*one|highest|top|main)?\s*priority\s*(?:today\s*)?(?:is|:)\s*",
    re.I,
)


# ---------------------------------------------------------------- state

def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"emails": {}}


def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def day_record(state, addr, date):
    person = state["emails"].setdefault(addr, {"days": {}})
    return person["days"].setdefault(date, {
        "priority": None, "done": False, "asked": False,
        "checkins": [], "done_notified": False,
    })


# ---------------------------------------------------------------- email i/o

def smtp_send(cfg, to_addr, subject, body, dry_run=False):
    print(f"SEND -> {to_addr} | {subject!r}: {body}")
    if dry_run:
        return
    msg = EmailMessage()
    msg["From"] = cfg["address"]
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)
    ctx = ssl.create_default_context()
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as s:
        s.starttls(context=ctx)
        s.login(cfg["address"], cfg["password"])
        s.send_message(msg)


def extract_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and \
                    "attachment" not in str(part.get("Content-Disposition", "")):
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(part.get_content_charset() or "utf-8",
                                          errors="replace")
        return ""
    payload = msg.get_payload(decode=True)
    if payload:
        return payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
    return msg.get_payload() or ""


def strip_quoted(text):
    lines = []
    for line in text.splitlines():
        if line.lstrip().startswith(">"):
            break
        if any(m.match(line.strip()) for m in QUOTE_MARKERS):
            break
        lines.append(line)
    return "\n".join(lines).strip()


def clean_priority(text):
    return PRIORITY_PREFIX.sub("", text).strip().rstrip(".")


def fetch_unseen(cfg):
    """Return [(from_addr, reply_text)] for unseen inbox mail, marking it seen."""
    out = []
    imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    try:
        imap.login(cfg["address"], cfg["password"])
        imap.select("INBOX")
        typ, data = imap.search(None, "UNSEEN")
        if typ != "OK":
            return out
        for num in data[0].split():
            typ, msg_data = imap.fetch(num, "(BODY.PEEK[])")
            if typ != "OK" or not msg_data or not msg_data[0]:
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            from_addr = parseaddr(msg.get("From", ""))[1].lower()
            reply = strip_quoted(extract_body(msg))
            out.append((from_addr, reply))
            imap.store(num, "+FLAGS", "\\Seen")
    finally:
        try:
            imap.logout()
        except Exception:
            pass
    return out


# ---------------------------------------------------------------- logic

def process_replies(state, cfg, date):
    for from_addr, reply in fetch_unseen(cfg):
        if from_addr not in cfg["recipients"]:
            print(f"Ignoring reply from non-configured address: {from_addr}")
            continue
        if not reply:
            continue
        rec = day_record(state, from_addr, date)
        if rec["priority"] and looks_done(reply):
            rec["done"] = True
            print(f"Marked done for {from_addr}: {rec['priority']!r}")
        else:
            rec["priority"] = clean_priority(reply)
            rec["done"] = False
            rec["done_notified"] = False
            print(f"Set priority for {from_addr}: {rec['priority']!r}")


def send_morning(state, cfg, date, dry_run=False):
    for addr in cfg["recipients"]:
        rec = day_record(state, addr, date)
        if rec["asked"]:
            continue
        smtp_send(cfg, addr, SUBJECT,
                  "Good morning! What's your #1 priority for today?\n\n"
                  "Just reply to this email. I'll check in through the day -- "
                  "reply DONE when you've finished it.", dry_run)
        rec["asked"] = True


def send_checkins(state, cfg, date, hour, dry_run=False):
    for addr in cfg["recipients"]:
        rec = day_record(state, addr, date)
        if hour in rec["checkins"]:
            continue
        if not rec["priority"]:
            smtp_send(cfg, addr, "Re: " + SUBJECT,
                      "Haven't heard your #1 priority yet today -- what is it?",
                      dry_run)
        elif rec["done"]:
            if rec["done_notified"]:
                continue
            smtp_send(cfg, addr, "Re: " + SUBJECT,
                      f"Nice work finishing \"{rec['priority']}\"! "
                      "Anything else you want to line up?", dry_run)
            rec["done_notified"] = True
        else:
            smtp_send(cfg, addr, "Re: " + SUBJECT,
                      f"Check-in: is your #1 (\"{rec['priority']}\") done yet? "
                      "Reply DONE when it is.", dry_run)
        rec["checkins"].append(hour)


def run(cfg, now, dry_run=False, force=None):
    date = now.strftime("%Y-%m-%d")
    state = load_state()

    if not dry_run:
        process_replies(state, cfg, date)

    hour = now.hour
    do_morning = force == "morning" or (force is None and hour == MORNING_HOUR)
    do_checkin = force == "checkin" or (force is None and hour in CHECKIN_HOURS)

    if do_morning:
        send_morning(state, cfg, date, dry_run)
    if do_checkin:
        send_checkins(state, cfg, date, hour if hour in CHECKIN_HOURS else CHECKIN_HOURS[0], dry_run)
    if not (do_morning or do_checkin):
        print(f"No send slot at {now:%H:%M} ET; processed replies only.")

    if not dry_run:
        save_state(state)


def need(name):
    val = os.environ.get(name)
    if not val:
        sys.exit(f"Missing required environment variable: {name}")
    return val


def main():
    ap = argparse.ArgumentParser(description="Daily priority email check-in.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print intended sends without IMAP/SMTP or creds.")
    ap.add_argument("--force", choices=["morning", "checkin"],
                    help="Force a mode regardless of the current hour.")
    args = ap.parse_args()

    now = datetime.now(ET)

    if args.dry_run:
        cfg = {"address": "bot@example.com", "password": "x",
               "recipients": ["you@example.com"]}
    else:
        recipients = [a.strip().lower() for a in need("CONVERSATION_EMAILS").split(",") if a.strip()]
        cfg = {
            "address": need("GMAIL_ADDRESS"),
            "password": need("GMAIL_APP_PASSWORD"),
            "recipients": recipients,
        }

    run(cfg, now, dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    main()

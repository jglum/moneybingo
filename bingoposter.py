import json, os, random, time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# --- Config from env ---
TOKEN = os.environ["SLACK_BOT_TOKEN"]
CHANNEL = os.environ["SLACK_CHANNEL_ID"]
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

# Post time: 2:30 PM America/New_York
TARGET_HOUR = 14
TARGET_MINUTE = 30
TZ = ZoneInfo("America/New_York")

STATE_PATH = Path("bingo_state.json")

def letter_for(num: int) -> str:
    if 1 <= num <= 15: return "B"
    if 16 <= num <= 30: return "I"
    if 31 <= num <= 45: return "N"
    if 46 <= num <= 60: return "G"
    return "O"

def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"remaining": list(range(1, 76)), "history": []}

def save_state(state):
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True))
    tmp.replace(STATE_PATH)

def pick_number(state):
    if not state["remaining"]:
        state["remaining"] = list(range(1, 76))
        state["history"].clear()
    choice = random.choice(state["remaining"])
    state["remaining"].remove(choice)
    state["history"].append({"n": choice, "ts": int(time.time())})
    return choice

def build_blocks(n: int, called_count: int):
    b = letter_for(n)
    label = f"{b}{n:02d}"
    return [
        {"type": "header", "text": {"type": "plain_text", "text": "🎱 Daily Bingo"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Number:* `{label}` 🎉"}},
        {"type": "context", "elements": [
            {"type": "mrkdwn", "text": f"_{called_count}/75 called this round_"}
        ]}
    ]

def main():
    # Only post at exactly 14:30 New York time
    now_ny = datetime.now(TZ)
    if not (now_ny.hour == TARGET_HOUR and now_ny.minute == TARGET_MINUTE):
        print(f"[INFO] Current NY time {now_ny.strftime('%Y-%m-%d %H:%M')}, not posting.")
        return

    state = load_state()
    num = pick_number(state)
    save_state(state)

    called_so_far = 75 - len(state["remaining"])
    blocks = build_blocks(num, called_so_far)

    if DRY_RUN:
        print("[DRY RUN] Would post:")
        print(json.dumps(blocks, indent=2))
        return

    client = WebClient(token=TOKEN)
    try:
        client.chat_postMessage(channel=CHANNEL, text="Daily Bingo", blocks=blocks)
        print(f"[OK] Posted number {letter_for(num)}{num}")
    except SlackApiError as e:
        print(f"[ERROR] Slack API: {e.response.get('error')}")

if __name__ == "__main__":
    main()

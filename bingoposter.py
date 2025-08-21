import json, os, random, time
from pathlib import Path
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# --- Config from env ---
TOKEN = os.environ["SLACK_BOT_TOKEN"]
CHANNEL = os.environ["SLACK_CHANNEL_ID"]

# --- Storage (kept in the repo so it persists between runs) ---
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
    # Avoid flakiness: write atomically
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True))
    tmp.replace(STATE_PATH)

def pick_number(state):
    if not state["remaining"]:
        # Reset after finishing a full set
        state["remaining"] = list(range(1, 76))
        state["history"].clear()

    choice = random.choice(state["remaining"])
    state["remaining"].remove(choice)
    state["history"].append({"n": choice, "ts": int(time.time())})
    return choice

def post_message(client, text):
    client.chat_postMessage(channel=CHANNEL, text=text)

def main():
    client = WebClient(token=TOKEN)
    state = load_state()
    num = pick_number(state)
    save_state(state)

    msg = f"*Daily Bingo:* {letter_for(num)}{num:02d}  🎉"
    # Add a friendly footer showing how many have been called this round
    msg += f"\n_{75 - len(state['remaining'])}/75 called this round_"
    try:
        post_message(client, msg)
    except SlackApiError as e:
        # Post errors to the channel for visibility (optional)
        err = f"Failed to post bingo number: {e.response.get('error')}"
        print(err)
        raise

if __name__ == "__main__":
    main()


import requests
import os
import re
import json
from datetime import datetime, timezone

# ================= CONFIG =================
URL = "https://www.wowauctions.net/auctionHouse/chromie-craft/chromiecraft/mergedAh/bold-stormjewel-45862"
PROXY_URL = f"https://r.jina.ai/{URL}"
STATE_FILE = "state.json"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
DISCORD_USER_ID = "203262759113195520"
TIMEOUT = 20
BLOCK_REMINDER_RUNS = 6       # Remind every 6 blocked runs (~2 hours at 20min intervals)
STALE_THRESHOLD_MINUTES = 20  # Alert if data is older than this
# ==========================================

# -------- Load state ----------------------
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
else:
    state = {}

state.setdefault("last_price", None)
state.setdefault("last_amount", None)
state.setdefault("jina_blocked", False)
state.setdefault("blocked_run_count", 0)
state.setdefault("stale_alerted", False)

# -------- Fetch page ----------------------
try:
    response = requests.get(PROXY_URL, timeout=TIMEOUT, headers={"x-no-cache": "true"})
    response.raise_for_status()
    text = response.text.lower()

    # Jina recovered after a block → alert
    if state["jina_blocked"]:
        print("Jina access restored → alert triggered")
        if WEBHOOK_URL:
            requests.post(WEBHOOK_URL, json={
                "content": f"<@{DISCORD_USER_ID}> ✅ Auction bot is back online! Jina access restored."
            })
        state["jina_blocked"] = False
        state["blocked_run_count"] = 0

except requests.exceptions.HTTPError as e:
    if e.response.status_code == 451:
        state["blocked_run_count"] += 1
        print(f"Jina blocked (451) → run {state['blocked_run_count']}")

        first_block = not state["jina_blocked"]
        reminder_due = state["blocked_run_count"] % BLOCK_REMINDER_RUNS == 0

        if (first_block or reminder_due) and WEBHOOK_URL:
            hours_blocked = (state["blocked_run_count"] * 20) // 60
            mins_blocked = (state["blocked_run_count"] * 20) % 60
            duration = f"{hours_blocked}h {mins_blocked}m" if hours_blocked else f"{mins_blocked}m"
            requests.post(WEBHOOK_URL, json={
                "content": f"<@{DISCORD_USER_ID}> ⚠️ Auction bot is blocked (451 Legal Error). Has been down for ~{duration}. Will retry next run."
            })

        state["jina_blocked"] = True
    else:
        print("HTTP error:", e)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    exit()

except Exception as e:
    print("Request failed:", e)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    exit()

# -------- Check data freshness ------------
scan_match = re.search(r"last scan of this ah:.*?\((\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) utc\)", text)
if scan_match:
    try:
        scan_time = datetime.strptime(scan_match.group(1), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        minutes_old = (now - scan_time).total_seconds() / 60
        print(f"Data last scanned: {scan_match.group(1)} ({minutes_old:.1f}m ago)")

        if minutes_old > STALE_THRESHOLD_MINUTES:
            if not state["stale_alerted"] and WEBHOOK_URL:
                requests.post(WEBHOOK_URL, json={
                    "content": f"<@{DISCORD_USER_ID}> ⏰ Warning: Auction data hasn't been updated in {minutes_old:.1f} minutes. Results may be outdated."
                })
            state["stale_alerted"] = True
        else:
            state["stale_alerted"] = False
    except Exception as e:
        print("Could not parse scan time:", e)
else:
    print("Could not find last scanned timestamp in page")

# -------- Parse page ----------------------
on_ah = "not on the auction house right now" not in text

amount_match = re.search(r"amount\s+(\d+)", text)
amount = int(amount_match.group(1)) if amount_match else 0

price_match = re.search(
    r"minimum buyout\s+(\d+)\s*g(?:\s*(\d+)\s*s)?(?:\s*(\d+)\s*c)?",text
)
if price_match:
    g = int(price_match.group(1))
    s = int(price_match.group(2) or 0)
    c = int(price_match.group(3) or 0)
    price = g * 10000 + s * 100 + c
else:
    price = None

gold_price = price // 10000 if price else None

print(f"Item on AH: {on_ah}")
print(f"Amount: {amount}")
print(f"Price: {gold_price}g" if gold_price else "Price not found")

# -------- Alert logic ---------------------
if on_ah and price:
    if state["last_price"] is None:
        print("New listing detected → alert triggered")
        alert_needed = True
    elif price < state["last_price"]:
        print("Price undercut detected → alert triggered")
        alert_needed = True
    else:
        alert_needed = False

    if alert_needed and WEBHOOK_URL:
        content = f"<@{DISCORD_USER_ID}> 🔥 Bold Stormjewel is on AH! Price: {gold_price}g | Amount: {amount}"
        requests.post(WEBHOOK_URL, json={"content": content})
        print("Discord alert sent!")

    state["last_price"] = price
    state["last_amount"] = amount
else:
    if state["last_price"] is not None:
        print("Item removed from AH → wiping memory")
    state["last_price"] = None
    state["last_amount"] = None

# -------- Save state ----------------------
with open(STATE_FILE, "w") as f:
    json.dump(state, f)

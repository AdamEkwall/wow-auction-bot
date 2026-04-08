import requests
import os
import re
import json

# ================= CONFIG =================
URL = "https://www.wowauctions.net/auctionHouse/chromie-craft/chromiecraft/mergedAh/bold-stormjewel-45862"
PROXY_URL = f"https://r.jina.ai/{URL}"
STATE_FILE = "state.json"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
DISCORD_USER_ID = "203262759113195520"
TIMEOUT = 20
# ==========================================

# -------- Load state ----------------------
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
else:
    state = {}

state.setdefault("last_price", None)
state.setdefault("last_amount", None)

# -------- Fetch page ----------------------
try:
    response = requests.get(PROXY_URL, timeout=TIMEOUT, headers={"x-no-cache": "true"})
    response.raise_for_status()
    text = response.text.lower()
except Exception as e:
    print("Request failed:", e)
    exit()

# -------- Parse page ----------------------
on_ah = "not on the auction house right now" not in text

amount_match = re.search(r"amount\s+(\d+)", text)
amount = int(amount_match.group(1)) if amount_match else 0

price_match = re.search(
    r"minimum buyout\s+(\d+)\s*g(?:\s*(\d+)\s*s)?(?:\s*(\d+)\s*c)?", text
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

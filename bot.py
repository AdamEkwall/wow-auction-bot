import requests
import os
import re
import json
import subprocess

# ================= CONFIG =================
URL = "https://www.wowauctions.net/auctionHouse/chromie-craft/chromiecraft/mergedAh/bold-stormjewel-45862"
PROXY_URL = f"https://r.jina.ai/{URL}"
STATE_FILE = "state.json"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
DISCORD_USER_ID = "203262759113195520"
TIMEOUT = 20  # seconds
BRANCH = "auction-state"
# =========================================

# -------- Ensure we are on the state branch -------------
subprocess.run(["git", "fetch", "origin", BRANCH], check=False)
subprocess.run(["git", "checkout", "-B", BRANCH], check=True)

# -------- Load previous state -------------
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
else:
    state = {}

state.setdefault("last_price", None)
state.setdefault("last_amount", None)

# -------- Fetch page via proxy ------------
try:
    response = requests.get(
        PROXY_URL,
        timeout=TIMEOUT,
        headers={"x-no-cache": "true"}
    )
    response.raise_for_status()
    text = response.text.lower()
except Exception as e:
    print("Request failed:", e)
    exit()

# -------- Check if item is on AH ----------
if "not on the auction house right now" in text:
    on_ah = False
else:
    on_ah = True

# -------- Extract Amount ------------------
amount_match = re.search(r"amount\s+(\d+)", text)
amount = int(amount_match.group(1)) if amount_match else 0

# -------- Extract Price (gold/silver/copper) ---------
price_match = re.search(r"minimum buyout\s+(\d+)\s*g(?:\s*(\d+)\s*s)?(?:\s*(\d+)\s*c)?", text)
if price_match:
    g = int(price_match.group(1))
    s = int(price_match.group(2) or 0)
    c = int(price_match.group(3) or 0)
    price = g * 10000 + s * 100 + c  # total in copper
else:
    price = None

gold_price = price // 10000 if price else None

# -------- Verification output ---------------
print(f"Item on AH: {on_ah}")
print(f"Amount: {amount}")
print(f"Price: {gold_price}g" if gold_price else "Price not found")

# -------- Alert logic ----------------------
alert_needed = False

if on_ah and price:
    # New logic: wipe memory if only one item is listed and price increased
    if state["last_price"] is None:
        alert_needed = True
    elif price < state["last_price"]:
        alert_needed = True
    elif amount != state.get("last_amount", 0):
        alert_needed = True
    elif amount == 1 and state["last_price"] and price > state["last_price"]:
        # New listing with higher price, reset memory
        state["last_price"] = None
        state["last_amount"] = None
        alert_needed = True

    if alert_needed and WEBHOOK_URL:
        content = f"<@{DISCORD_USER_ID}> 🔥 Bold Stormjewel is on AH! Price: {gold_price}g | Amount: {amount}"
        requests.post(WEBHOOK_URL, json={"content": content})
        print("Discord alert sent!")
else:
    print("Item not currently listed.")
    # Wipe memory if no listing
    state["last_price"] = None
    state["last_amount"] = None

# -------- Update state ---------------------
state["last_price"] = price if on_ah else None
state["last_amount"] = amount if on_ah else None

with open(STATE_FILE, "w") as f:
    json.dump(state, f)

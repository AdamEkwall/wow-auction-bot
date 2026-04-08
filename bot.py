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
TIMEOUT = 20  # seconds
# =========================================

# -------- Load previous state -------------
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
else:
    state = {}

state.setdefault("last_price", None)
state.setdefault("last_amount", None)
state.setdefault("last_alert_price", None)
state.setdefault("last_alert_amount", None)

# -------- Fetch page via proxy ------------
try:
    response = requests.get(
        PROXY_URL,
        timeout=TIMEOUT,
        headers={"x-no-cache": "true"}  # prevent caching
    )
    response.raise_for_status()
    text = response.text.lower()
except Exception as e:
    print("Request failed:", e)
    exit()

# -------- Check if item is on AH ----------
on_ah = "not on the auction house right now" not in text

# -------- Extract Amount ------------------
amount_match = re.search(r"amount\s+(\d+)", text)
amount = int(amount_match.group(1)) if amount_match else 0

# -------- Extract Price (gold/silver/copper) ---------
price_match = re.search(
    r"minimum buyout\s+(\d+)\s*g(?:\s*(\d+)\s*s)?(?:\s*(\d+)\s*c)?", text
)
if price_match:
    g = int(price_match.group(1))
    s = int(price_match.group(2) or 0)
    c = int(price_match.group(3) or 0)
    price = g * 10000 + s * 100 + c  # total in copper
else:
    price = None

# -------- Convert to gold for printing -------
gold_price = price // 10000 if price else None

# -------- Verification output ---------------
print(f"Item on AH: {on_ah}")
print(f"Amount: {amount}")
print(f"Price: {gold_price}g" if gold_price else "Price not found")

# -------- Compute unique listing ID ---------
listing_id = f"{price}_{amount}" if price else None
last_alert_id = f"{state.get('last_alert_price')}_{state.get('last_alert_amount')}"

# -------- Alert logic ----------------------
alert_needed = False

if on_ah and price:
    # wipe memory if single higher-price listing
    if amount == 1 and state["last_price"] and price > state["last_price"]:
        print("Single listing higher than previous → wiping memory")
        state["last_price"] = None
        state["last_amount"] = None
        state["last_alert_price"] = None
        state["last_alert_amount"] = None

    # check if this is a new auction to alert
    if listing_id != last_alert_id:
        alert_needed = True
    else:
        alert_needed = False

    if alert_needed and WEBHOOK_URL:
        content = f"<@{DISCORD_USER_ID}> 🔥 Bold Stormjewel is on AH! Price: {gold_price}g | Amount: {amount}"
        requests.post(WEBHOOK_URL, json={"content": content})
        print("Discord alert sent!")
        # store what we just alerted
        state["last_alert_price"] = price
        state["last_alert_amount"] = amount

else:
    # item removed → wipe all state
    if state["last_price"] is not None:
        print("Item removed from AH → wiping memory")
    state["last_price"] = None
    state["last_amount"] = None
    state["last_alert_price"] = None
    state["last_alert_amount"] = None
    print("Item not currently listed.")

# -------- Update last seen state ---------------------
state["last_price"] = price if on_ah else None
state["last_amount"] = amount if on_ah else None

with open(STATE_FILE, "w") as f:
    json.dump(state, f)

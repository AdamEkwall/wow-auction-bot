import requests
import os
import json

# CONFIG
BUILD_ID = "Q3nbXdN5bJfNCngEBsXEq"
URL = f"https://www.wowauctions.net/_next/data/{BUILD_ID}/auctionHouse/chromie-craft/chromiecraft/mergedAh/bold-stormjewel-45862.json"

STATE_FILE = "state.json"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
DISCORD_USER_ID = "203262759113195520"

# Load state
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
else:
    state = {}

state.setdefault("last_price", None)

# Request data
headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers)

if response.status_code != 200:
    print("Request failed:", response.status_code)
    print(response.text[:300])
    exit()

data = response.json()

# Extract values
stats = data["pageProps"]["item"]["stats"]

price = stats["minimum_buyout"]
amount = stats["item_count"]

# Convert copper → gold
gold = price // 10000

print(f"Price: {gold}g | Amount: {amount}")

# Detect listing
if amount > 0:
    alert_needed = False

    if state["last_price"] is None:
        alert_needed = True
    elif price < state["last_price"]:
        alert_needed = True

    if alert_needed:
        content = f"<@{DISCORD_USER_ID}> 🔥 Bold Stormjewel is on AH! Price: {gold}g | Amount: {amount}"
        requests.post(WEBHOOK_URL, json={"content": content})
        print("Discord alert sent!")

    state["last_price"] = price
else:
    print("Item not currently listed.")

# Save state
with open(STATE_FILE, "w") as f:
    json.dump(state, f)

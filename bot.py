import os
import json
import requests

# CONFIG
ITEM_URL = "https://www.wowauctions.net/_next/data/Q3nbXdN5bJfNCngEBsXEq/auctionHouse/chromie-craft/chromiecraft/mergedAh/bold-stormjewel-45862.json"
STATE_FILE = "state.json"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
DISCORD_USER_ID = "203262759113195520"  # @Ekwall

# Load previous state
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
else:
    state = {}

# Ensure keys exist
state.setdefault("last_price", None)
state.setdefault("last_amount", None)

# Fetch JSON data
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0",
    "Accept": "*/*",
    "Referer": "https://www.wowauctions.net/",
    "x-nextjs-data": "1",
}
response = requests.get(ITEM_URL, headers=headers)

if response.status_code != 200:
    print(f"Request failed: {response.status_code}")
    print(response.text[:500])  # preview
    exit(1)

# Parse JSON safely
try:
    data = response.json()
except json.JSONDecodeError as e:
    print("Failed to parse JSON:", e)
    exit(1)

# Extract values
item = data["pageProps"]["item"]
stats = item["stats"]

price = stats.get("minimum_buyout", 0)
amount = stats.get("item_count", 0)
gold = price // 10000  # convert copper → gold

print(f"Price: {gold}g | Amount: {amount}")

# Detect if item is actually on AH
item_on_ah = False

# Primary check
if amount > 0:
    item_on_ah = True

# Secondary safety check (tooltip text)
tooltip = item.get("tooltip", "")
if "not on the auction house right now" in tooltip.lower():
    item_on_ah = False

if not item_on_ah:
    print("Item not on AH.")
else:
    alert_needed = False

    # Determine if alert should be sent
    if state["last_price"] is None:
        alert_needed = True
    elif gold < state["last_price"]:
        alert_needed = True

    if alert_needed:
        content = f"<@{DISCORD_USER_ID}> 🔥 Bold Stormjewel is on AH! Price: {gold}g | Amount: {amount}"
        requests.post(WEBHOOK_URL, json={"content": content})
        print("Discord alert sent!")

# Update state
state["last_price"] = gold
state["last_amount"] = amount

# Save state
with open(STATE_FILE, "w") as f:
    json.dump(state, f)

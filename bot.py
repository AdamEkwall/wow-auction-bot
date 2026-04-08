import requests
import os
import json
import re

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

# Fetch via proxy (optional, keeps Cloudflare away)
proxy_url = f"https://r.jina.ai/{URL}"
response = requests.get(proxy_url)

if response.status_code != 200:
    print("Request failed:", response.status_code)
    print(response.text[:300])
    exit()

text = response.text

# 🔥 Extract JSON from wrapped response
start = text.find("{")
end = text.rfind("}") + 1

if start == -1 or end == -1:
    print("Could not find JSON in response")
    exit()

json_text = text[start:end]

# Remove problematic tooltip field (contains broken HTML)
json_text = re.sub(r'"tooltip":.*?"\}', '"tooltip":""}', json_text)

# Fix escaped line breaks
json_text = json_text.replace("\n", "").replace("\r", "")

data = json.loads(json_text)

# Extract stats and timestamps
item = data["pageProps"]["item"]
stats = item["stats"]

price = stats["minimum_buyout"]
amount = stats["item_count"]

# Use timestamps to check if item is currently on AH
item_last_seen = stats["item_last_seen"]
realm_last_scan = item.get("realm_last_scan", item_last_seen)  # fallback if missing

item_on_ah = (item_last_seen == realm_last_scan)

# Convert copper → gold
gold = price // 10000 if price else 0

print(f"item_last_seen: {item_last_seen}")
print(f"realm_last_scan: {realm_last_scan}")
print(f"Item on AH: {item_on_ah}")
print(f"Price: {gold}g | Amount: {amount}")

# Alert logic
if item_on_ah:
    alert_needed = False

    if state["last_price"] is None:
        alert_needed = True
    elif price < state["last_price"]:
        alert_needed = True

    if alert_needed:
        content = f"<@{DISCORD_USER_ID}> 🔥 Bold Stormjewel is on AH! Price: {gold}g | Amount: {amount}"
        requests.post(WEBHOOK_URL, json={"content": content})
        print("Discord alert sent!")

    # Update state
    state["last_price"] = price
else:
    print("Item not currently listed.")

# Save state
with open(STATE_FILE, "w") as f:
    json.dump(state, f)

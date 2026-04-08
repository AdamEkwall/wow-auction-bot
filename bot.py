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

# Load previous state
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
else:
    state = {}

state.setdefault("last_price", None)

# Fetch via proxy
response = requests.get(f"https://r.jina.ai/{URL}", timeout=20)
if response.status_code != 200:
    print("Request failed:", response.status_code)
    exit()

text = response.text

# Extract JSON start/end
start = text.find('{"pageProps"')
end = text.rfind("}") + 1
if start == -1 or end == -1:
    print("Could not extract JSON")
    exit()

json_text = text[start:end]

# --- Remove tooltip and any other problematic keys ---
# Matches: "tooltip": anything until the next } or ,
pattern = r'"tooltip"\s*:\s*"(?:\\.|[^"\\])*"\s*,?'
json_text = re.sub(pattern, '', json_text, flags=re.DOTALL)

# Remove newlines
json_text = json_text.replace("\n", "").replace("\r", "")

# Now parse JSON
try:
    data = json.loads(json_text)
except json.JSONDecodeError as e:
    print("JSON parsing failed:", e)
    exit()

# Extract values
item = data["pageProps"]["item"]
stats = item["stats"]

price = stats.get("minimum_buyout", 0)
amount = stats.get("item_count", 0)

# Convert copper → gold
gold = price // 10000 if price else 0

# Detect if item is currently on AH
item_last_seen = stats.get("item_last_seen")
realm_last_scan = item.get("realm_last_scan")
item_on_ah = (item_last_seen == realm_last_scan)

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

    state["last_price"] = price
else:
    print("Item not currently listed.")

# Save state
with open(STATE_FILE, "w") as f:
    json.dump(state, f)

import requests
import os
import json
import time
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

# Fetch via proxy
def fetch_data():
    proxy_url = f"https://r.jina.ai/{URL}"
    for attempt in range(2):
        try:
            response = requests.get(proxy_url, timeout=20)
            if response.status_code == 200:
                return response.text
            print(f"Attempt {attempt+1} failed with status:", response.status_code)
        except Exception as e:
            print(f"Attempt {attempt+1} error:", e)
        time.sleep(2)
    return None

text = fetch_data()
if not text:
    print("Failed to fetch data.")
    exit()

# Extract JSON from wrapped response
start = text.find('{"pageProps"')
end = text.rfind("}") + 1
if start == -1 or end == -1:
    print("Could not extract JSON")
    exit()
json_text = text[start:end]

# ✅ Clean problematic tooltip field safely
# Tooltip contains HTML with unescaped line breaks or quotes
# We replace it with an empty string
json_text = re.sub(r'"tooltip":\s*".*?"', '"tooltip":""', json_text, flags=re.DOTALL)

# Fix escaped line breaks
json_text = json_text.replace("\n", "").replace("\r", "")

# Parse JSON
try:
    data = json.loads(json_text)
except Exception as e:
    print("JSON parsing failed:", e)
    exit()

# Extract values
item = data["pageProps"]["item"]
stats = item["stats"]

price = stats.get("minimum_buyout", 0)
amount = stats.get("item_count", 0)

# Convert copper → gold
gold = price // 10000 if price else 0

# Correct AH detection
item_last_seen = stats["item_last_seen"]
realm_last_scan = item["realm_last_scan"]
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

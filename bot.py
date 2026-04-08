import requests
import os
import re

URL = "https://www.wowauctions.net/auctionHouse/chromie-craft/chromiecraft/mergedAh/bold-stormjewel-45862"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
DISCORD_USER_ID = "203262759113195520"

# Fetch via jina proxy
proxy_url = f"https://r.jina.ai/{URL}"
response = requests.get(proxy_url, timeout=20)

if response.status_code != 200:
    print("Request failed:", response.status_code)
    exit()

text = response.text.lower()

# ❌ Check if item is NOT on AH
if "not on the auction house right now" in text:
    print("Item not on AH.")
    exit()

print("Item IS on AH!")

# 🔍 Extract price (minimum buyout)
price_match = re.search(r"minimum buyout\s+(\d+)\s*g", text)

# 🔍 Extract amount
amount_match = re.search(r"amount\s+(\d+)", text)

price = int(price_match.group(1)) if price_match else None
amount = int(amount_match.group(1)) if amount_match else None

print(f"Price: {price}g | Amount: {amount}")

# Send Discord alert
if WEBHOOK_URL:
    content = f"<@{DISCORD_USER_ID}> 🔥 Bold Stormjewel is on AH! Price: {price}g | Amount: {amount}"
    requests.post(WEBHOOK_URL, json={"content": content})
    print("Discord alert sent!")

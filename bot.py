import requests
import os

URL = "https://www.wowauctions.net/auctionHouse/chromie-craft/chromiecraft/mergedAh/bold-stormjewel-45862"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
DISCORD_USER_ID = "203262759113195520"

# Fetch page via jina proxy
proxy_url = f"https://r.jina.ai/{URL}"
response = requests.get(proxy_url, timeout=20)

if response.status_code != 200:
    print("Request failed:", response.status_code)
    exit()

text = response.text.lower()

# 🔍 Detect if item is NOT on AH
if "not on the auction house right now" in text:
    print("Item not on AH.")
else:
    print("Item IS on AH!")

    # Optional: send Discord alert
    if WEBHOOK_URL:
        content = f"<@{DISCORD_USER_ID}> 🔥 Bold Stormjewel is on AH!"
        requests.post(WEBHOOK_URL, json={"content": content})
        print("Discord alert sent!")

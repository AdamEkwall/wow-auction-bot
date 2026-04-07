import os
import json
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# CONFIG
URL = "https://www.wowauctions.net/auctionHouse/chromie-craft/chromiecraft/mergedAh/bold-stormjewel-45862"
STATE_FILE = "state.json"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
DISCORD_USER_ID = "203262759113195520"  # @ekwall

# Load previous state
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
else:
    state = {"last_price": None, "last_amount": None}

# Setup headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=chrome_options)
driver.get(URL)

# Wait for JS to load
time.sleep(5)

# Parse page
soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

# Detect if item is on AH
def item_exists(soup):
    text = soup.get_text().lower()
    if "not on the auction house right now" in text:
        return False
    return True

# Parse price and amount
def get_price_and_amount(soup):
    text = soup.get_text()
    price = None
    amount = None

    for line in text.split("\n"):
        line = line.strip()
        if "minimum buyout" in line.lower():
            # Extract numbers only
            price = int(''.join(filter(str.isdigit, line)))
        if "amount" in line.lower():
            amount = int(''.join(filter(str.isdigit, line)))
    return price, amount

# Main logic
if not item_exists(soup):
    print("Item not on AH.")
else:
    price, amount = get_price_and_amount(soup)
    print(f"Found AH item: Price={price}, Amount={amount}")

    alert_needed = False

    if state["last_price"] is None:
        alert_needed = True
    elif price < state["last_price"]:
        alert_needed = True

    if alert_needed:
        content = f"<@{DISCORD_USER_ID}> 🔥 Bold Stormjewel is on AH! Price: {price}g | Amount: {amount}"
        requests.post(WEBHOOK_URL, json={"content": content})
        print("Discord alert sent!")

    # Update state
    state["last_price"] = price
    state["last_amount"] = amount

# Save state
with open(STATE_FILE, "w") as f:
    json.dump(state, f)

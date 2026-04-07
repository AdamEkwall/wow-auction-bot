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
    state = {}

# Ensure keys exist (prevents crash)
state.setdefault("last_price", None)
state.setdefault("last_amount", None)

# Setup headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

from selenium.webdriver.chrome.service import Service

service = Service("/usr/bin/chromedriver")
chrome_options.binary_location = "/usr/bin/chromium-browser"

driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get(URL)

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    # Wait up to 15 seconds for "Minimum Buyout" to appear in the page
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Minimum Buyout')]"))
    )
except:
    print("Timeout waiting for auction data")

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
import re

def get_price_and_amount(soup):
    text = soup.get_text(separator="\n").lower()
    price = None
    amount = None

    for line in text.split("\n"):
        line = line.strip()

        # Minimum Buyout
        if "minimum buyout" in line:
            match = re.search(r'minimum buyout\s+(\d+)', line)
            if match:
                price = int(match.group(1))

        # Amount or Quantity
        if "amount" in line or "quantity" in line:
            match = re.search(r'(?:amount|quantity)\s+(\d+)', line)
            if match:
                amount = int(match.group(1))

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
    elif price is not None and state["last_price"] is not None and price < state["last_price"]:
        alert_needed = True
    elif price == state.get("last_price") and amount != state.get("last_amount"):
        alert_needed = True

    if alert_needed:
        content = f"<@{DISCORD_USER_ID}> 🔥 Bold Stormjewel is on AH! Price: {price}g | Amount: {amount}"
        requests.post(WEBHOOK_URL, json={"content": content})
        print("Discord alert sent!")

    # Update state
    state["last_price"] = price
    state["last_amount"] = amount
    # Update state
    state["last_price"] = price
    state["last_amount"] = amount

# Save state
with open(STATE_FILE, "w") as f:
    json.dump(state, f)

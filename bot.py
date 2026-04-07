import os
import json
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# ---------------- CONFIG ----------------
URL = "https://www.wowauctions.net/auctionHouse/chromie-craft/chromiecraft/mergedAh/bold-stormjewel-45862"
STATE_FILE = "state.json"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
DISCORD_USER_ID = "203262759113195520"  # @ekwall
WAIT_SECONDS = 5  # wait for JS to load

# ---------------- LOAD STATE ----------------
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
else:
    state = {}

# Ensure keys exist
state.setdefault("last_price", None)
state.setdefault("last_amount", None)

# ---------------- SETUP SELENIUM ----------------
chrome_options = Options()
chrome_options.add_argument("--headless=new")  # new headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.binary_location = "/usr/bin/chromium-browser"

service = Service("/usr/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=chrome_options)

driver.get(URL)
time.sleep(WAIT_SECONDS)  # wait for JS to load

# ---------------- PARSE PAGE ----------------
soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

text = soup.get_text(separator="\n").lower()

# ---------------- CHECK IF ITEM EXISTS ----------------
def item_exists(text):
    return "not on the auction house right now" not in text

# ---------------- PARSE PRICE AND AMOUNT ----------------
def get_price_and_amount(text):
    price = None
    amount = None
    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        # Parse amount
        if line.startswith("current prices amount"):
            try:
                parts = line.split()
                idx_amount = parts.index("amount")
                amount = int(parts[idx_amount + 1])
            except Exception as e:
                print("Failed to parse amount:", e)
        # Parse minimum buyout
        if "minimum buyout" in line:
            try:
                parts = line.replace("g", "").split()
                idx_mb = parts.index("minimum")  # word "minimum"
                price = int(parts[idx_mb + 2])  # 2 words after "minimum" = number
            except Exception as e:
                print("Failed to parse price:", e)
    return price, amount

# ---------------- MAIN LOGIC ----------------
if not item_exists(text):
    print("Item not on AH.")
else:
    price, amount = get_price_and_amount(text)
    print(f"Found AH item: Price={price}, Amount={amount}")

    alert_needed = False

    # Always alert if first scan
    if state["last_price"] is None:
        alert_needed = True
    # Alert if price dropped
    elif price is not None and (state["last_price"] is None or price < state["last_price"]):
        alert_needed = True

    if alert_needed and price is not None and amount is not None:
        content = f"<@{DISCORD_USER_ID}> 🔥 Bold Stormjewel is on AH! Price: {price}g | Amount: {amount}"
        try:
            requests.post(WEBHOOK_URL, json={"content": content})
            print("Discord alert sent!")
        except Exception as e:
            print("Failed to send Discord alert:", e)

    # Update state
    if price is not None:
        state["last_price"] = price
    if amount is not None:
        state["last_amount"] = amount

# ---------------- SAVE STATE ----------------
with open(STATE_FILE, "w") as f:
    json.dump(state, f)

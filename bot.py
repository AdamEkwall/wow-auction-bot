import requests
from bs4 import BeautifulSoup
import json
import os

URL = "https://www.wowauctions.net/auctionHouse/chromie-craft/chromiecraft/mergedAh/bold-stormjewel-45862"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

STATE_FILE = "state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"last_scan": None, "lowest_price": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def get_page():
    response = requests.get(URL, timeout=10)
    return BeautifulSoup(response.text, "html.parser")

def get_last_scan(soup):
    text = soup.get_text().lower()
    for line in text.split("\n"):
        if "last scan" in line:
            return line.strip()
    return None

def item_exists(soup):
    text = soup.get_text().lower()

    if "not on the auction house right now" in text:
        return False
    if "no auctions of this item right now" in text:
        return False

    return True

def get_price_and_amount(soup):
    text = soup.get_text().lower()

    price = None
    amount = None

    for line in text.split("\n"):
        if "minimum buyout" in line:
            price = int(''.join(filter(str.isdigit, line)))
        if "amount" in line:
            amount = int(''.join(filter(str.isdigit, line)))

    return price, amount

def send_alert(message):
    # IMPORTANT: replace with real Discord mention ID if needed
    content = f"<203262759113195520> {message}"
    requests.post(WEBHOOK_URL, json={"content": content})

def main():
    send_alert("✅ TEST MESSAGE — bot is working!")

if __name__ == "__main__":
    main()

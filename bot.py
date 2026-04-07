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

def get_lowest_price(soup):
    text = soup.get_text().lower()

    if "no auctions of this item right now" in text:
        return None

    prices = []
    for td in soup.find_all("td"):
        t = td.get_text(strip=True).replace(",", "")
        if any(char.isdigit() for char in t):
            try:
                price = int(''.join(filter(str.isdigit, t)))
                prices.append(price)
            except:
                continue

    return min(prices) if prices else None

def send_alert(message):
    requests.post(WEBHOOK_URL, json={"content": message})

def main():
    state = load_state()
    soup = get_page()

    current_scan = get_last_scan(soup)

    # Only proceed if new scan
    if current_scan == state["last_scan"]:
        print("No new scan yet.")
        return

    print("New scan detected!")

    state["last_scan"] = current_scan

    current_price = get_lowest_price(soup)

    if current_price is None:
        print("No auctions found.")
        save_state(state)
        return

    previous_price = state.get("lowest_price")

    # Notify conditions
    if previous_price is None:
        send_alert(f"🔥 Bold Stormjewel is now on AH! Price: {current_price}g")
    elif current_price < previous_price:
        send_alert(f"💰 Cheaper Bold Stormjewel found! New price: {current_price}g (was {previous_price}g)")

    state["lowest_price"] = current_price
    save_state(state)

if __name__ == "__main__":
    main()

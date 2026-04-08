import requests

url = "https://www.wowauctions.net/_next/data/Q3nbXdN5bJfNCngEBsXEq/index.json"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*"
}

response = requests.get(url, headers=headers)

print("STATUS:", response.status_code)
print(response.text[:1000])

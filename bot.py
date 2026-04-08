import requests

url = "https://api.wowauctions.net/items/stats/30d/chromiecraft/mergedAh/45862"

response = requests.get(url)
data = response.json()

print(data)

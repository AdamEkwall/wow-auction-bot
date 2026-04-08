import requests

url = "https://api.wowauctions.net/items/stats/30d/chromiecraft/mergedAh/45862"

response = requests.get(url)

print("STATUS:", response.status_code)
print("TEXT PREVIEW:")
print(response.text[:500])  # print first 500 chars

import requests

url = "https://redsky.target.com/redsky_aggregations/v1/web/plp_search_v2"

params = {
    "key": "9f36aeafbe60771e321a7cc95a78140772ab3e96",
    "channel": "WEB",
    "count": 24,
    "keyword": "pokemon trading card",
    "offset": 0,
    "platform": "desktop",
    "useragent": "Mozilla/5.0",
    "visitor_id": "AAA"
}

headers = {
    "User-Agent": "Mozilla/5.0"
}

res = requests.get(url, params=params, headers=headers)
res.raise_for_status()
data = res.json()

for product in data["data"]["search"]["products"]:
    tcin = product["tcin"]
    title = product["item"]["product_description"]["title"]
    print(f"TCIN: {tcin} - Title: {title}")

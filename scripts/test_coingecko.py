import requests
import json

url = "https://api.coingecko.com/api/v3/coins/markets"
params = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 10,
    "page": 1,
    "sparkline": "false"
}

try:
    print(f"Fetching {url}...")
    response = requests.get(url, params=params, timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Got {len(data)} coins")
        print(json.dumps(data[0], indent=2))
    else:
        print(response.text)
except Exception as e:
    print(f"Error: {e}")

import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("TWELVE_DATA_KEY")

BASE_URL = "https://api.twelvedata.com/price"

def fetch_price(symbol):
	params = {"symbol": symbol, "apikey": API_KEY}
	response = requests.get(BASE_URL,params=params)
	data = response.json ()
	print(data)
	return float(data["price"])

btc = fetch_price("BTC/USD")
GOLD = fetch_price("XAU/USD")

print(f"BTC:  {btc:,.2f}")
print(f"Gold: {GOLD:,.2f}")
print(f"Ratio: {btc / GOLD:.4f}")

import csv
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()
API_KEY = os.getenv("TWELVE_DATA_KEY")
if not API_KEY:
    raise SystemExit("TWELVE_DATA_KEY not found - check .env exists in this directory")

HISTORY_FILE = "history.csv"

def fetch_series(symbol, outputsize):
    params = {"symbol": symbol, "interval": "1day",
              "outputsize": outputsize, "apikey": API_KEY}
    response = requests.get("https://api.twelvedata.com/time_series", params=params)
    data = response.json()
    if "values" not in data:
        raise SystemExit(f"API error for {symbol}: {data.get('message', data)}")
    return {row["datetime"]: float(row["close"]) for row in data["values"]}

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    with open(HISTORY_FILE, newline="") as f:
        return {row["date"]: row for row in csv.DictReader(f)}

def save_history(history):
    with open(HISTORY_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "btc", "gold", "ratio"])
        writer.writeheader()
        for day in sorted(history):
            writer.writerow(history[day])

history = load_history()
outputsize = 250 if not history else 10   # seed on first run, backfill after

btc = fetch_series("BTC/USD", outputsize)
gold = fetch_series("XAU/USD", outputsize)

last_gold = None
for day in sorted(btc):
    if day in gold:
        last_gold = gold[day]        # forward-fill: weekends reuse Friday's close
    if last_gold is None:
        continue                     # BTC dates before the first gold close we have
    ratio = btc[day] / last_gold
    history[day] = {"date": day, "btc": f"{btc[day]:.2f}",
                    "gold": f"{last_gold:.2f}", "ratio": f"{ratio:.4f}"}

save_history(history)
print(f"{len(history)} rows in history; latest: {max(history)} "
      f"ratio {history[max(history)]['ratio']}")

MA_WINDOW = 50

days = sorted(history)                       # chronological list of date strings
ratios = [float(history[d]["ratio"]) for d in days]

ma = []
for i in range(len(ratios)):
    if i + 1 < MA_WINDOW:
        ma.append(None)                      # not enough history yet
    else:
        window = ratios[i + 1 - MA_WINDOW : i + 1]
        ma.append(round(sum(window) / MA_WINDOW, 4))

latest_ratio = ratios[-1]
latest_ma = ma[-1]
state = "above" if latest_ratio > latest_ma else "below"

def list_art(state):
    folder = os.path.join("art", state)
    if not os.path.isdir(folder):
        return []
    exts = (".png", ".jpg", ".jpeg", ".webp", ".gif")
    return sorted(f"{folder}/{name}" for name in os.listdir(folder)
                  if name.lower().endswith(exts))

art = {"above": list_art("above"), "below": list_art("below")}

output = {
    "updated": days[-1],
    "ma_window": MA_WINDOW,
    "latest": {"ratio": latest_ratio, "ma": latest_ma, "state": state},
    "art": art,
    "series": [{"date": d, "ratio": r, "ma": m}
               for d, r, m in zip(days, ratios, ma)],
}

with open("data.js", "w") as f:
    f.write("const DATA = " + json.dumps(output, indent=2) + ";\n")

print(f"{days[-1]}: ratio {latest_ratio:.4f}, MA{MA_WINDOW} {latest_ma:.4f} -> {state}")

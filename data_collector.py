import requests
import datetime
import csv
import os
import pandas as pd

FILE_NAME = "data_log.csv"
WEATHER_API = "https://api.open-meteo.com/v1/forecast?latitude=30.74&longitude=76.78&current=temperature_2m"
BTC_API = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"

def fetch_data():
    try:
        # Fetch weather data
        weather_resp = requests.get(WEATHER_API, timeout=10).json()
        temperature = weather_resp["current"]["temperature_2m"]

        # Fetch Bitcoin price from CoinGecko
        btc_resp = requests.get(BTC_API, timeout=10).json()
        btc_price = btc_resp["bitcoin"]["usd"]

        # Timestamp
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        return [timestamp, temperature, btc_price]

    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def ensure_file():
    if not os.path.exists(FILE_NAME):
        with open(FILE_NAME, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Temperature (°C)", "Bitcoin Price (USD)"])

def trim_old_data():
    try:
        df = pd.read_csv(FILE_NAME)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True)
        one_week_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        df = df[df["Timestamp"] > one_week_ago]
        df.to_csv(FILE_NAME, index=False)
    except Exception as e:
        print(f"Error trimming data: {e}")

def main():
    ensure_file()
    new_data = fetch_data()
    if new_data:
        with open(FILE_NAME, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(new_data)
        trim_old_data()
        print(f"✅ Logged: {new_data}")

if __name__ == "__main__":
    main()

import requests
import datetime
import csv
import os
import pandas as pd
import time

FILE_NAME = "data_log.csv"
WEATHER_API = "https://api.open-meteo.com/v1/forecast?latitude=30.74&longitude=76.78&current=temperature_2m"
BTC_API = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"

# --- Utility: Retry Wrapper ---
def fetch_with_retry(url, retries=3, delay=5):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Attempt {attempt + 1}/{retries} failed for {url}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return None

def fetch_data():
    temperature = "N/A"
    btc_price = "N/A"

    # --- Weather ---
    weather_data = fetch_with_retry(WEATHER_API)
    if weather_data:
        try:
            temperature = weather_data["current"]["temperature_2m"]
        except Exception as e:
            print(f"Failed to parse weather data: {e}")

    # --- Bitcoin ---
    btc_data = fetch_with_retry(BTC_API)
    if btc_data:
        try:
            btc_price = btc_data["bitcoin"]["usd"]
        except Exception as e:
            print(f"Failed to parse BTC data: {e}")

    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    return [timestamp, temperature, btc_price]

def ensure_file():
    if not os.path.exists(FILE_NAME):
        with open(FILE_NAME, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Temperature (°C)", "Bitcoin Price (USD)"])

def trim_old_data():
    try:
        df = pd.read_csv(FILE_NAME)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True)
        one_week_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).replace(tzinfo=datetime.timezone.utc)
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

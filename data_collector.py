#!/usr/bin/env python3
import requests
import datetime
import csv
import os
import pandas as pd
import time
import pytz
import tempfile

# ---------- Config ----------
FILE_NAME = "data_log.csv"
WEATHER_API = "https://api.open-meteo.com/v1/forecast?latitude=30.74&longitude=76.78&current=temperature_2m"
BTC_API = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
RETRIES = 3
RETRY_DELAY = 3
DAYS_TO_KEEP = 7
HEADER = ["Timestamp", "Temperature (°C)", "Bitcoin Price (USD)"]

IST = pytz.timezone("Asia/Kolkata")

# ---------- Helpers ----------
def fetch_with_retry(url, retries=RETRIES, delay=RETRY_DELAY, timeout=10):
    for i in range(retries):
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if i < retries - 1:
                time.sleep(delay)
            else:
                return None

def ensure_file():
    if not os.path.exists(FILE_NAME):
        with open(FILE_NAME, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(HEADER)

def read_last_row():
    """Return last data row as list or None if file empty (excluding header)."""
    if not os.path.exists(FILE_NAME):
        return None
    try:
        with open(FILE_NAME, "r", newline="", encoding="utf-8") as f:
            rows = f.read().strip().splitlines()
            if len(rows) <= 1:
                return None
            last = rows[-1].split(",")
            return [c.strip() for c in last]
    except Exception:
        return None

def atomic_write_csv(rows):
    """Write rows (list of lists) atomically to FILE_NAME."""
    fd, tmp_path = tempfile.mkstemp(prefix="tmp_data_", suffix=".csv")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as tmpf:
            writer = csv.writer(tmpf)
            writer.writerows(rows)
        os.replace(tmp_path, FILE_NAME)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

# ---------- Data operations ----------
def get_temperature():
    data = fetch_with_retry(WEATHER_API)
    if not data:
        return None
    try:
        return data["current"]["temperature_2m"]
    except Exception:
        return None

def get_bitcoin_price():
    data = fetch_with_retry(BTC_API)
    if not data:
        return None
    try:
        return data["bitcoin"]["usd"]
    except Exception:
        return None

def trim_old_data():
    try:
        df = pd.read_csv(FILE_NAME)
        # Parse timestamps robustly; coerce invalid -> NaT
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True, errors="coerce")
        df = df.dropna(subset=["Timestamp"])
        # Convert to IST timezone for filtering
        df["Timestamp"] = df["Timestamp"].dt.tz_convert(IST)
        cutoff = datetime.datetime.now(IST) - datetime.timedelta(days=DAYS_TO_KEEP)
        filtered = df[df["Timestamp"] > cutoff]
        # Convert back to ISO8601 (Grafana friendly)
        filtered["Timestamp"] = filtered["Timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S%z")
        # Write back only if rows changed
        if len(filtered) != len(df):
            filtered.to_csv(FILE_NAME, index=False)
            print(f"Trimmed -> kept {len(filtered)} rows")
    except Exception:
        pass

# ---------- Main ----------
def main():
    ensure_file()

    # fetch data
    temp = get_temperature()
    btc = get_bitcoin_price()

    # prepare IST timestamp (ISO 8601 format)
    now_ist = datetime.datetime.now(IST).replace(microsecond=0)
    timestamp = now_ist.isoformat()

    # validate fetched values; if missing, mark as "N/A"
    temp_val = temp if temp is not None else "N/A"
    btc_val = btc if btc is not None else "N/A"

    new_row = [timestamp, temp_val, btc_val]

    # read last row to avoid duplicate writes if values identical
    last = read_last_row()
    if last and len(last) >= 3:
        last_values = [last[1], last[2]]
        new_values = [str(new_row[1]), str(new_row[2])]
        if last_values == new_values:
            print("No change, skipped")
            return

    # Append new row safely:
    try:
        rows = []
        if os.path.exists(FILE_NAME):
            with open(FILE_NAME, "r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
        if not rows or rows[0] != HEADER:
            rows = [HEADER]
        rows.append(new_row)
        atomic_write_csv(rows)
        trim_old_data()
        print("✅ Logged successfully:", new_row)
    except Exception as e:
        print("ERROR: write failed:", e)

if __name__ == "__main__":
    main()

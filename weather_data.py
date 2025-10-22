import requests
import datetime
import csv
import os

# --- Configuration ---
FILE_NAME = "weather_log.csv"
LAT = 30.74
LON = 76.78
HEADERS = ["Timestamp", "Temperature (°C)", "PM2.5"]
DAYS_TO_KEEP = 7  # Keep last 7 days

# --- API URLs ---
TEMP_API_URL = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=temperature_2m"
AQ_API_URL = f"https://api.openaq.org/v3/latest?coordinates={LAT},{LON}&radius=100000&parameter=pm25"

# --- Functions ---
def get_temperature():
    try:
        response = requests.get(TEMP_API_URL)
        response.raise_for_status()
        data = response.json()
        return data["current"]["temperature_2m"]
    except Exception as e:
        print(f"Temperature API Error: {e}")
        return None

def get_air_quality():
    try:
        response = requests.get(AQ_API_URL)
        response.raise_for_status()
        data = response.json()

        # v3 API returns results -> measurements
        if "results" in data and len(data["results"]) > 0:
            measurements = data["results"][0].get("measurements", [])
            for m in measurements:
                if m.get("parameter") == "pm25":
                    return m.get("value")
        print("No PM2.5 data found in v3 API response.")
        return None

    except Exception as e:
        print(f"Air Quality API Error: {e}")
        return None

# --- Load existing CSV ---
all_data = []
if not os.path.exists(FILE_NAME):
    all_data.append(HEADERS)
else:
    try:
        with open(FILE_NAME, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            all_data = list(reader)
        if not all_data or all_data[0] != HEADERS:
            all_data = [HEADERS]
    except Exception:
        all_data = [HEADERS]

# --- Fetch new data ---
temp_value = get_temperature()
pm25_value = get_air_quality()
timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if temp_value is not None and pm25_value is not None:
    all_data.append([timestamp, temp_value, pm25_value])
    print(f"[{timestamp}] Temp: {temp_value}°C, PM2.5: {pm25_value}")
else:
    print("Invalid API data. Skipping this run.")

# --- Keep only last 7 days of data ---
cutoff = datetime.datetime.now() - datetime.timedelta(days=DAYS_TO_KEEP)
cleaned_data = [all_data[0]]  # header
for row in all_data[1:]:
    try:
        row_time = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        if row_time >= cutoff:
            cleaned_data.append(row)
    except Exception:
        continue

# --- Write CSV ---
try:
    with open(FILE_NAME, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(cleaned_data)
    print(f"Data saved. Total entries: {len(cleaned_data)-1}")
except Exception as e:
    print(f"Error writing CSV: {e}")

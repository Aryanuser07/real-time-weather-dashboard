import requests
import datetime
import csv
import os

# --- Configuration ---
FILE_NAME = "weather_log.csv"
LAT = 30.74
LON = 76.78
HEADERS = ["Timestamp", "Temperature (°C)", "PM2.5"]
DAYS_TO_KEEP = 7  # Keep only last 7 days of data

# --- API URLs ---
TEMP_API_URL = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=temperature_2m"
AQ_API_URL = f"https://api.openaq.org/v2/latest?coordinates={LAT},{LON}&radius=10000&parameter=pm25"

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
        if data['results']:
            for measurement in data['results'][0]['measurements']:
                if measurement['parameter'] == 'pm25':
                    return measurement['value']
        print("No PM2.5 data found in API response.")
        return None
    except Exception as e:
        print(f"Air Quality API Error: {e}")
        return None

# --- Load existing data ---
all_data = []
if not os.path.exists(FILE_NAME):
    all_data.append(HEADERS)
else:
    try:
        with open(FILE_NAME, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            all_data = list(reader)
        if not all_data or all_data[0] != HEADERS:
            all_data = [HEADERS]
    except Exception as e:
        print(f"Error reading file: {e}")
        all_data = [HEADERS]

# --- Fetch new data ---
temp_value = get_temperature()
pm25_value = get_air_quality()
timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if temp_value is not None and pm25_value is not None:
    new_row = [timestamp, temp_value, pm25_value]
    all_data.append(new_row)
    print(f"[{timestamp}] Temp: {temp_value}°C, PM2.5: {pm25_value}")
else:
    print("Invalid API data. Skipping this run.")

# --- Remove entries older than 7 days ---
cutoff = datetime.datetime.now() - datetime.timedelta(days=DAYS_TO_KEEP)
cleaned_data = [all_data[0]]  # header
for row in all_data[1:]:
    try:
        row_time = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        if row_time >= cutoff:
            cleaned_data.append(row)
    except Exception:
        continue  # skip invalid rows

# --- Write back cleaned data ---
try:
    with open(FILE_NAME, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(cleaned_data)
    print(f"Data saved. Total entries: {len(cleaned_data)-1}")
except Exception as e:
    print(f"Error writing file: {e}")

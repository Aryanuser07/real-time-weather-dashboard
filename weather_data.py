import requests
import datetime
import csv
import time
import os

# --- Configuration ---
FILE_NAME = "weather_log.csv"
MAX_ROWS = 500
LAT = 30.74 # Temperature ke liye abhi bhi zaroori hai
LON = 76.78
HEADERS = ["Timestamp", "Temperature (°C)", "PM2.5"]

# --- API KEY (Reads from GitHub Secrets) ---
OPENAQ_KEY = os.environ.get('OPENAQ_API_KEY') 

# --- API URLs ---
TEMP_API_URL = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=temperature_2m"
# --- !!! 404 FIX: Ab hum coordinates ki jagah direct v3 LOCATION ID (213346) use kar rahe hain !!! ---
AQ_API_URL = "https://api.openaq.org/v3/measurements?locations_id=213346&parameter=pm25&limit=1&order_by=datetime&sort=desc"


# --- Function to fetch Temperature ---
def get_temperature():
    try:
        response = requests.get(TEMP_API_URL)
        response.raise_for_status()
        data = response.json()
        return data["current"]["temperature_2m"]
    except Exception as e:
        print(f"Temperature API Error: {e}")
        return None

# --- Function to fetch Air Quality (PM2.5) ---
def get_air_quality():
    if not OPENAQ_KEY:
        print("Error: OPENAQ_API_KEY secret not found! Check GitHub Settings > Secrets.")
        return None
        
    try:
        headers = {
            "accept": "application/json",
            "X-API-Key": OPENAQ_KEY
        }
        response = requests.get(AQ_API_URL, headers=headers)
        response.raise_for_status() # Check for 401/404 errors
        data = response.json()
        
        # JSON structure: results[0].value
        if data['results'] and len(data['results']) > 0:
            pm25_value = data['results'][0]['value']
            return pm25_value
        
        print(f"No PM2.5 data found for location ID 213346.")
        return None
    except Exception as e:
        print(f"Air Quality API Error: {e}") 
        return None

# --- Main Program (Baaki sab same hai) ---
print("Starting Logger (Single Run with Log Rotation)...")

all_data = []
if not os.path.exists(FILE_NAME):
    print(f"Log file not found. Creating new file: {FILE_NAME}")
    all_data.append(HEADERS)
else:
    try:
        with open(FILE_NAME, 'r', newline='', encoding='latin-1') as file:
            reader = csv.reader(file)
            all_data = list(reader)
        if not all_data or all_data[0] != HEADERS:
             print("Header mismatch or empty file. Recreating file.")
             all_data = [HEADERS]
    except Exception as e:
        print(f"Error reading file {e}. Recreating.")
        all_data = [HEADERS]

try:
    temp_value = get_temperature()
    pm25_value = get_air_quality()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if temp_value is not None and pm25_value is not None:
        new_row = [timestamp, temp_value, pm25_value]
        all_data.append(new_row)
        print(f"[{timestamp}] Temp: {temp_value}°C, PM2.5: {pm25_value}")
    else:
        print("Invalid data from API (one or both failed). Skipping this run.")
except Exception as e:
    print(f"An unexpected error occurred fetching data: {e}")

if len(all_data) > (MAX_ROWS + 1): # +1 for the header
    print(f"Log rotating: Trimming from {len(all_data)-1} to {MAX_ROWS} entries.")
    header = all_data[0]
    data_rows = all_data[1:]
    trimmed_data = data_rows[-MAX_ROWS:]
    all_data = [header] + trimmed_data

try:
    with open(FILE_NAME, "w", newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(all_data)
    print(f"Data written to {FILE_NAME}. Total entries: {len(all_data)-1}")
except Exception as e:
    print(f"Error writing to file: {e}")

print("Script finished.")

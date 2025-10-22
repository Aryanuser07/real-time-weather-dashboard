import requests
import datetime
import csv
import time
import os

# --- Configuration ---
FILE_NAME = "weather_log.csv"
MAX_ROWS = 500 # File mein hamesha last 500 rows hi rakhega
LAT = 30.74
LON = 76.78
HEADERS = ["Timestamp", "Temperature (°C)", "PM2.5"] # Headers ko define karlo

# API URLs
TEMP_API_URL = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=temperature_2m"
AQ_API_URL = f"https://api.openaq.org/v2/latest?limit=1&page=1&offset=0&sort=desc&coordinates={LAT},{LON}&radius=100000&order_by=lastUpdated&dumpRaw=false"


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
    try:
        response = requests.get(AQ_API_URL)
        response.raise_for_status()
        data = response.json()
        for measurement in data['results'][0]['measurements']:
            if measurement['parameter'] == 'pm25':
                return measurement['value']
        return None
    except Exception as e:
        print(f"Air Quality API Error: {e}")
        return None

# --- Main Program (Single Run + Log Rotation) ---
print("Starting Logger (Single Run with Log Rotation)...")

# --- 1. Read existing data ---
all_data = []
if not os.path.exists(FILE_NAME):
    print(f"Log file not found. Creating new file: {FILE_NAME}")
    all_data.append(HEADERS)
else:
    try:
        with open(FILE_NAME, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            all_data = list(reader)
        # Check if header is correct or file is empty
        if not all_data or all_data[0] != HEADERS:
             print("Header mismatch or empty file. Recreating file.")
             all_data = [HEADERS]
    except Exception as e:
        print(f"Error reading file {e}. Recreating.")
        all_data = [HEADERS]

# --- 2. Fetch new data ---
try:
    temp_value = get_temperature()
    pm25_value = get_air_quality()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Add new data IF data is valid
    if temp_value is not None and pm25_value is not None:
        new_row = [timestamp, temp_value, pm25_value]
        all_data.append(new_row)
        print(f"[{timestamp}] Temp: {temp_value}°C, PM2.5: {pm25_value}")
    else:
        print("Invalid data from API. Skipping this run.")

except Exception as e:
    print(f"An unexpected error occurred fetching data: {e}")

# --- 3. Rotate Log (Keep only last MAX_ROWS) ---
if len(all_data) > (MAX_ROWS + 1): # +1 for the header
    print(f"Log rotating: Trimming from {len(all_data)-1} to {MAX_ROWS} entries.")
    # Keep the header + the last MAX_ROWS data
    header = all_data[0]
    data_rows = all_data[1:] # Get just the data
    trimmed_data = data_rows[-MAX_ROWS:] # Get the last 500
    all_data = [header] + trimmed_data # Re-assemble the file

# --- 4. Write cleaned data back to file ---
try:
    with open(FILE_NAME, "w", newline='', encoding='utf-8') as file: # "w" = OVERWRITE
        writer = csv.writer(file)
        writer.writerows(all_data)
    print(f"Data written to {FILE_NAME}. Total entries: {len(all_data)-1}")
except Exception as e:
    print(f"Error writing to file: {e}")

print("Script finished.")

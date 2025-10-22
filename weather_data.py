import requests
import datetime
import csv
import time
import os

# --- Configuration ---
FILE_NAME = "weather_log.csv"
# Chandigarh Coordinates (Aap badal sakte hain)
LAT = 30.74
LON = 76.78

# API URLs
TEMP_API_URL = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=temperature_2m"
# OpenAQ API (Chandigarh ke paas ka latest data)
AQ_API_URL = f"https://api.openaq.org/v2/latest?limit=1&page=1&offset=0&sort=desc&coordinates={LAT},{LON}&radius=100000&order_by=lastUpdated&dumpRaw=false"


# --- Function to fetch Temperature ---
def get_temperature():
    try:
        response = requests.get(TEMP_API_URL)
        response.raise_for_status() # Check for errors
        data = response.json()
        temperature = data["current"]["temperature_2m"]
        return temperature
    except Exception as e:
        print(f"Temperature API Error: {e}")
        return None # Return None if error

# --- Function to fetch Air Quality (PM2.5) ---
def get_air_quality():
    try:
        response = requests.get(AQ_API_URL)
        response.raise_for_status()
        data = response.json()
        # Find PM2.5 measurement from the results
        for measurement in data['results'][0]['measurements']:
            if measurement['parameter'] == 'pm25':
                pm25 = measurement['value']
                return pm25
        return None # Return None if pm25 not found
    except Exception as e:
        print(f"Air Quality API Error: {e}")
        return None # Return None if error

# --- Main Program ---
print("Starting Real-Time Data Logger (Temp + AQI)...")

# --- 1. Write Header Only If File Does Not Exist ---
if not os.path.exists(FILE_NAME):
    with open(FILE_NAME, "w", newline="") as file:
        writer = csv.writer(file)
        # Naye 3-column headers
        writer.writerow(["Timestamp", "Temperature (°C)", "PM2.5"])
    print(f"Created new log file: {FILE_NAME}")

# --- 2. Main Data Logging Loop ---
while True:
    try:
        # Fetch data from both APIs
        temp_value = get_temperature()
        pm25_value = get_air_quality()

        # Format timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Log to Console
        print(f"[{timestamp}] Temp: {temp_value}°C, PM2.5: {pm25_value}")

        # --- Save data to CSV ---
        with open(FILE_NAME, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, temp_value, pm25_value])

    except Exception as e:
        print(f"An unexpected error occurred in main loop: {e}")

    # Wait for 10 minutes (600 seconds)
    print("Waiting for 10 minutes...")
    time.sleep(600)
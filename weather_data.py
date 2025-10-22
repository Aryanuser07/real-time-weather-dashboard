import requests
import csv
import os
from datetime import datetime

# --- 1. API Configuration (Yahan apni details daalo) ---

# OpenWeatherMap API details (Temperature ke liye)
WEATHER_API_KEY = "YOUR_OPENWEATHER_API_KEY"  # Apna API Key yahan daalo
CITY_NAME = "YOUR_CITY_NAME"  # Apna sheher yahan daalo (e.g., "Mumbai,IN")
weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY_NAME}&appid={WEATHER_API_KEY}&units=metric"

# CoinGecko API details (Bitcoin ke liye - Iske liye API key nahi chahiye)
btc_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"


# --- 2. Data Fetching Functions ---

def get_temperature():
    """Mausam ka data fetch karta hai."""
    try:
        response = requests.get(weather_url)
        response.raise_for_status()  # Agar koi error ho (jaise 404, 500) toh exception raise karo
        data = response.json()
        temperature = data['main']['temp']
        return temperature
    except Exception as e:
        print(f"Error fetching temperature: {e}")
        return None  # Error hone par None return karo

def get_btc_price():
    """Bitcoin ka price fetch karta hai."""
    try:
        response = requests.get(btc_url)
        response.raise_for_status()
        data = response.json()
        price = data['bitcoin']['usd']
        return price
    except Exception as e:
        print(f"Error fetching BTC price: {e}")
        return None  # Error hone par None return karo


# --- 3. Main Script Logic ---

print("Data logging script shuru ho raha hai...")

# Data fetch karo
current_temp = get_temperature()
current_btc = get_btc_price()

# Timestamp generate karo (UTC time, jaisa GitHub Actions use karta hai)
current_timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

# Check karo ki data sahi se aaya ya nahi
if current_temp is not None and current_btc is not None:
    
    csv_file_path = 'weather_log.csv'
    header_row = ['Timestamp', 'Temperature (°C)', 'BTC_Price_USD']
    data_row = [current_timestamp, current_temp, current_btc]

    # Check karo ki file pehle se hai ya nahi
    file_exists = os.path.isfile(csv_file_path)

    try:
        # File ko 'a' (append) mode mein kholo
        with open(csv_file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Agar file nayi hai (yaani exist nahi karti thi), toh header likho
            if not file_exists or os.path.getsize(csv_file_path) == 0:
                writer.writerow(header_row)
                print("File nahi thi, header row add kar raha hoon.")
            
            # Naya data row hamesha add karo
            writer.writerow(data_row)
            
        print(f"Successfully data append kiya: {data_row}")

    except Exception as e:
        print(f"CSV file mein likhne mein error: {e}")

else:
    print("Data fetch nahi kar paaya, CSV file update nahi kar raha.")

print("Script khatm.")

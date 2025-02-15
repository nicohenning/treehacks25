import os
import requests
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def get_lat_lon_from_address(address):
    """
    Convert an address into latitude & longitude using Google Maps API.
    """
    if not GOOGLE_MAPS_API_KEY:
        raise ValueError("Google Maps API key not found. Ensure it's set in the .env file.")

    url = f"https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": GOOGLE_MAPS_API_KEY
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data["status"] == "OK":
            location = data["results"][0]["geometry"]["location"]
            return location["lat"], location["lng"]
        else:
            print(f"Google Maps API Error: {data['status']}")
            return None, None
    else:
        print(f"❌ HTTP Error: {response.status_code} - {response.text}")
        return None, None


def get_average_yearly_temperature(lat, lon):
    """
    Get the average yearly temperature (°C) for given latitude & longitude.
    Uses Open-Meteo's climate API.
    """

    url = f"https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": "2019-01-01",  # Last 5 years
        "end_date": "2024-12-31",
        "daily": "temperature_2m_max",
        "temperature_unit": "celsius",
        "timezone": "auto"
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if "daily" in data and "temperature_2m_max" in data["daily"]:
            temperatures = data["daily"]["temperature_2m_max"]
            average_temp = sum(temperatures) / len(temperatures)  # Calculate mean temp
            return round(average_temp, 2)
        else:
            print("⚠️ Open-Meteo API response missing temperature data.")
            return None
    else:
        print(f"❌ HTTP Error: {response.status_code} - {response.text}")
        return None


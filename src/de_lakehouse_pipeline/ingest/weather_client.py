import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def fetch_current_weather(city: str = "Berkeley,US") -> dict:
    
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENWEATHER_API_KEY")

    params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
    }

    response = requests.get(BASE_URL, params=params, timeout=15)
    response.raise_for_status()
    return response.json()
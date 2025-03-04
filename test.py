import os
import math
import requests
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup

app = Flask(__name__)

STATIONS_URL = "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"
BASE_WEATHER_URL = "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/all/"
STATIONS_FILE = "ghcnd-stations.txt"
WEATHER_DATA_FILE = "ghcnd-weather.txt"


### 🔹 Hilfsfunktionen ###

def download_station_file():
    """Lädt die Stationsdatei herunter, falls sie nicht existiert."""
    if not os.path.exists(STATIONS_FILE):
        print("📥 Lade Stationsdatei herunter...")
        response = requests.get(STATIONS_URL)
        if response.status_code == 200:
            with open(STATIONS_FILE, "wb") as file:
                file.write(response.content)
            print("✅ Stationsdatei erfolgreich gespeichert.")
        else:
            print("❌ Fehler beim Herunterladen der Stationsdatei:", response.status_code)


def parse_stations():
    """Liest die `ghcnd-stations.txt` und speichert sie als Liste von Stationen."""
    stations = []
    if not os.path.exists(STATIONS_FILE):
        print(f"❌ Stationsdatei {STATIONS_FILE} nicht gefunden!")
        return stations

    with open(STATIONS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                station_id = line[0:11].strip()
                lat = float(line[12:20].strip())
                lon = float(line[21:30].strip())
                station_name = line[41:71].strip()
                stations.append({"id": station_id, "lat": lat, "lon": lon, "name": station_name})
            except ValueError:
                continue
    return stations


def haversine(lat1, lon1, lat2, lon2):
    """Berechnet die Entfernung zwischen zwei Punkten auf der Erde in Kilometern."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def save_weather_data(station_id, data):
    """Speichert Wetterdaten in einer lokalen Datei."""
    with open(WEATHER_DATA_FILE, "a", encoding="utf-8") as file:
        file.write(f"{station_id}:{data}\n")


def load_weather_data():
    """Lädt die gespeicherten Wetterdaten aus der Datei."""
    weather_data = {}
    if os.path.exists(WEATHER_DATA_FILE):
        with open(WEATHER_DATA_FILE, "r", encoding="utf-8") as file:
            for line in file:
                parts = line.strip().split(":", 1)
                if len(parts) == 2:
                    station_id, data = parts
                    weather_data[station_id] = eval(data)
    return weather_data


def download_weather_data_for_stations(station_ids):
    """
    Lädt die .dly-Dateien der gefundenen Stationen herunter und speichert sie in `ghcnd-weather.txt`.
    """
    for station_id in station_ids:
        file_url = BASE_WEATHER_URL + f"{station_id}.dly"
        print(f"📥 Lade Wetterdaten für {station_id} herunter...")

        response = requests.get(file_url)
        if response.status_code == 200:
            save_weather_data(station_id, response.text)
            print(f"✅ Wetterdaten für {station_id} gespeichert.")
        else:
            print(f"❌ Keine Wetterdaten für {station_id} gefunden.")


### 🔹 Flask Endpunkte ###

@app.route("/search_stations", methods=["GET"])
def search_stations():
    """Sucht Wetterstationen in einem gegebenen Radius."""
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
        radius = float(request.args.get("radius", 50))
        max_results = int(request.args.get("max", 10))
    except (TypeError, ValueError):
        return jsonify({"error": "Ungültige Parameter"}), 400

    # Stationen durchsuchen
    nearby_stations = []
    for station in stations:
        distance = haversine(lat, lon, station["lat"], station["lon"])
        if distance <= radius:
            station_copy = station.copy()
            station_copy["distance"] = round(distance, 2)
            nearby_stations.append(station_copy)

    # Stationen sortieren und begrenzen
    nearby_stations.sort(key=lambda x: x["distance"])
    selected_stations = nearby_stations[:max_results]

    # Wetterdaten für diese Stationen herunterladen
    station_ids = [station["id"] for station in selected_stations]
    download_weather_data_for_stations(station_ids)

    return jsonify(selected_stations)


@app.route("/get_station_data", methods=["GET"])
def get_station_data():
    """Gibt echte Wetterdaten aus der .dly-Datei zurück."""
    station_id = request.args.get("station_id")
    if not station_id:
        return jsonify({"error": "Station-ID fehlt"}), 400

    if station_id not in weather_data_cache:
        return jsonify({"error": f"Keine Wetterdaten für Station {station_id} gefunden."}), 404

    raw_data = weather_data_cache[station_id].split("\n")

    # 🔹 Temperaturdaten extrahieren
    annual_data = []
    seasonal_data = []
    temp_max = []
    temp_min = []

    for line in raw_data:
        if len(line) < 21:
            continue

        year = line[11:15].strip()
        element = line[17:21].strip()

        if element in ["TMAX", "TMIN"]:
            values = [int(line[i:i + 5]) / 10 for i in range(21, 261, 8) if line[i:i + 5].strip() != "-9999"]
            if element == "TMAX":
                temp_max.extend(values)
            else:
                temp_min.extend(values)

    if temp_max and temp_min:
        annual_data.append({
            "year": int(year),
            "annual_min": min(temp_min),
            "annual_max": max(temp_max)
        })

        seasonal_data.append({
            "year": int(year),
            "seasons": {
                "Winter": {"min": min(temp_min[:90]), "max": max(temp_max[:90])},
                "Spring": {"min": min(temp_min[90:180]), "max": max(temp_max[90:180])},
                "Summer": {"min": min(temp_min[180:270]), "max": max(temp_max[180:270])},
                "Autumn": {"min": min(temp_min[270:]), "max": max(temp_max[270:])}
            }
        })

    return jsonify({"station": station_id, "annual_data": annual_data, "seasonal_data": seasonal_data})


### 🔹 Initialisierung ###
download_station_file()
stations = parse_stations()
weather_data_cache = load_weather_data()  # Wetterdaten-Cache laden

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
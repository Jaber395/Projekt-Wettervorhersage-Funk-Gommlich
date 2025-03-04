import os
import math
import requests
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

STATIONS_URL = "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"
BASE_WEATHER_URL = "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/all/"
STATIONS_FILE = "ghcnd-stations.txt"
WEATHER_DATA_DIR = "ghcn_weather"

# Ordner für Wetterdaten anlegen
os.makedirs(WEATHER_DATA_DIR, exist_ok=True)

### 🔹 Hilfsfunktionen ###

def download_station_file():
    """Lädt die Stationsdatei herunter, falls sie nicht existiert."""
    if not os.path.exists(STATIONS_FILE):
        print("📥 Lade Stationsdatei herunter...")
        try:
            response = requests.get(STATIONS_URL, timeout=15)
            response.raise_for_status()
            with open(STATIONS_FILE, "wb") as file:
                file.write(response.content)
            print("✅ Stationsdatei erfolgreich gespeichert.")
        except requests.exceptions.RequestException as e:
            print("❌ Fehler beim Herunterladen der Stationsdatei:", e)

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

def download_weather_data(station_id):
    """Lädt Wetterdaten für eine Station herunter und speichert sie."""
    file_path = os.path.join(WEATHER_DATA_DIR, f"{station_id}.dly")
    if os.path.exists(file_path):
        print(f"📂 {station_id}.dly existiert bereits.")
        return
    
    url = f"{BASE_WEATHER_URL}{station_id}.dly"
    try:
        response = requests.get(url, timeout=20, stream=True)
        response.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ Wetterdaten für {station_id} gespeichert.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Fehler beim Download von {station_id}: {e}")

def download_weather_data_for_stations(station_ids):
    """Lädt Wetterdaten für mehrere Stationen parallel herunter."""
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(download_weather_data, station_ids)

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

    nearby_stations = [
        {**station, "distance": round(haversine(lat, lon, station["lat"], station["lon"]), 2)}
        for station in stations if haversine(lat, lon, station["lat"], station["lon"]) <= radius
    ]
    nearby_stations.sort(key=lambda x: x["distance"])
    selected_stations = nearby_stations[:max_results]

    station_ids = [station["id"] for station in selected_stations]
    download_weather_data_for_stations(station_ids)

    return jsonify(selected_stations)

@app.route("/get_station_data", methods=["GET"])
def get_station_data():
    """Gibt gespeicherte Wetterdaten zurück."""
    station_id = request.args.get("station_id")
    if not station_id:
        return jsonify({"error": "Station-ID fehlt"}), 400

    file_path = os.path.join(WEATHER_DATA_DIR, f"{station_id}.dly")
    if not os.path.exists(file_path):
        return jsonify({"error": f"Keine Wetterdaten für Station {station_id} gefunden."}), 404

    with open(file_path, "r", encoding="utf-8") as f:
        raw_data = f.readlines()
    return jsonify({"station": station_id, "data": raw_data[:100]})  # Max 100 Zeilen für Übersicht

### 🔹 Initialisierung ###
download_station_file()
stations = parse_stations()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

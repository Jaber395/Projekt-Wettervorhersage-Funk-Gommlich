import os
import requests
from flask import Flask, request, jsonify
import math
import random

app = Flask(__name__)

STATIONS_FILE = "ghcnd-stations.txt"
STATIONS_URL = "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"

def download_station_file():
    """Lädt die Stationsdaten herunter, falls die Datei nicht existiert."""
    if not os.path.exists(STATIONS_FILE):
        print("Stationsdatei wird heruntergeladen...")
        response = requests.get(STATIONS_URL)
        if response.status_code == 200:
            with open(STATIONS_FILE, "wb") as file:
                file.write(response.content)
            print("Download erfolgreich.")
        else:
            print("Fehler beim Download:", response.status_code)

def parse_stations():
    """Parst die heruntergeladene Stationsdatei und liefert eine Liste von Stationen zurück."""
    stations = []
    with open(STATIONS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            # NOAA-Format (fest definierte Spalten):
            # [0:11] Station-ID, [12:20] Latitude, [21:30] Longitude, [41:71] Stationsname
            station_id = line[0:11].strip()
            try:
                lat = float(line[12:20].strip())
                lon = float(line[21:30].strip())
            except ValueError:
                continue
            station_name = line[41:71].strip()
            stations.append({"id": station_id, "lat": lat, "lon": lon, "name": station_name})
    return stations

# Datei herunterladen (falls noch nicht vorhanden) und parsen
download_station_file()
stations = parse_stations()

def haversine(lat1, lon1, lat2, lon2):
    """Berechnet die Entfernung in Kilometern zwischen zwei Punkten anhand ihrer geographischen Koordinaten."""
    R = 6371  # Erdradius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@app.route("/search_stations", methods=["GET"])
def search_stations():
    """
    Sucht Stationen anhand geographischer Koordinaten, Suchradius und maximaler Anzahl.
    Parameter (als Query-Parameter):
      - lat: geographische Breite
      - lon: geographische Länge
      - radius: Suchradius in km (Standard: 50)
      - max: maximale Anzahl der zurückzuliefernden Stationen (Standard: 10)
    """
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
        radius = float(request.args.get("radius", 50))
        max_results = int(request.args.get("max", 10))
    except (TypeError, ValueError):
        return jsonify({"error": "Ungültige Parameter"}), 400

    nearby = []
    for station in stations:
        distance = haversine(lat, lon, station["lat"], station["lon"])
        if distance <= radius:
            station_copy = station.copy()
            station_copy["distance"] = round(distance, 2)
            nearby.append(station_copy)
    nearby.sort(key=lambda x: x["distance"])
    return jsonify(nearby[:max_results])

@app.route("/get_station_data", methods=["GET"])
def get_station_data():
    """
    Liefert (simulierte) aggregierte Wetterdaten für eine gewählte Station.
    Erwartete Query-Parameter:
      - station_id: ID der Station
      - start_year: Startjahr (Standard: 2010)
      - end_year: Endjahr (Standard: 2020)
    Es werden Dummy-Daten für:
      - Jährliche Mittelwerte (Minima und Maxima)
      - Saisonale Werte (Winter, Spring, Summer, Autumn)
    generiert.
    """
    station_id = request.args.get("station_id")
    try:
        start_year = int(request.args.get("start_year", 2010))
        end_year = int(request.args.get("end_year", 2020))
    except ValueError:
        return jsonify({"error": "Ungültige Jahresangaben"}), 400

    # Überprüfen, ob die Station existiert
    station = next((s for s in stations if s["id"] == station_id), None)
    if not station:
        return jsonify({"error": "Station nicht gefunden"}), 404

    annual_data = []
    seasonal_data = []
    for year in range(start_year, end_year + 1):
        # Dummy-Werte für jährliche Mittelwerte
        annual_min = round(random.uniform(-20, 10), 1)
        annual_max = round(random.uniform(10, 35), 1)
        annual_data.append({
            "year": year,
            "annual_min": annual_min,
            "annual_max": annual_max
        })

        # Dummy-Werte für saisonale Daten (4 meteorologische Jahreszeiten)
        seasons = ["Winter", "Spring", "Summer", "Autumn"]
        season_vals = {}
        for season in seasons:
            season_min = round(random.uniform(-20, 10), 1)
            season_max = round(random.uniform(10, 35), 1)
            season_vals[season] = {"min": season_min, "max": season_max}
        seasonal_data.append({
            "year": year,
            "seasons": season_vals
        })

    return jsonify({
        "station": station,
        "annual_data": annual_data,
        "seasonal_data": seasonal_data
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

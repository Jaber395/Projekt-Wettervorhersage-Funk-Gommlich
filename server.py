import os
import math
import gzip
from flask import Flask, request, jsonify

app = Flask(__name__)

STATIONS_FILE = "ghcnd-stations.txt"  # Beispiel-Stationendatei
WEATHER_DATA_DIR = "weather_data"  # Ordner für Wetterdaten

# Stationen werden hier zwischengespeichert (nach dem Parsen)
stations = []


### Hilfsfunktionen ###

def haversine(lat1, lon1, lat2, lon2):
    """Berechnet die Entfernung zwischen zwei Punkten auf der Erde in Kilometern."""
    R = 6371  # Erdradius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def parse_stations():
    """
    Parst die Datei mit den Stationen und gibt eine Liste mit Dictionaries zurück.
    Jede Station enthält: ID, Latitude, Longitude und Name.
    """
    parsed_stations = []
    if not os.path.exists(STATIONS_FILE):
        print(f"Die Datei {STATIONS_FILE} wurde nicht gefunden. Keine Stationen geladen.")
        return parsed_stations

    with open(STATIONS_FILE, "r", encoding="utf-8") as file:
        for line in file:
            try:
                # NOAA Stationsdatei hat ein festes Format
                station_id = line[0:11].strip()
                lat = float(line[12:20].strip())
                lon = float(line[21:30].strip())
                station_name = line[41:71].strip()
                parsed_stations.append({"id": station_id, "lat": lat, "lon": lon, "name": station_name})
            except ValueError:
                # Fehlerhafte Einträge überspringen
                continue
    print(f"{len(parsed_stations)} Stationen erfolgreich geladen.")
    return parsed_stations


### API-Endpunkte ###

@app.route("/search_stations", methods=["GET"])
def search_stations():
    """
    Sucht Stationen anhand geographischer Parameter und Suchradius.
    Erwartet: lat, lon, radius (km), max (max. Ergebnisse).
    """
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
        radius = float(request.args.get("radius", 50))  # Standardradius: 50 km
        max_results = int(request.args.get("max", 10))  # Standard: max. 10 Ergebnisse
    except (TypeError, ValueError):
        return jsonify({"error": "Ungültige Parameter"}), 400

    # Entfernungen berechnen und filtern
    nearby_stations = []
    for station in stations:
        distance = haversine(lat, lon, station["lat"], station["lon"])
        if distance <= radius:
            station_copy = station.copy()
            station_copy["distance"] = round(distance, 2)
            nearby_stations.append(station_copy)

    # Ergebnisse sortieren und begrenzen
    nearby_stations.sort(key=lambda x: x["distance"])
    return jsonify(nearby_stations[:max_results])


@app.route("/get_station_data", methods=["GET"])
def get_station_data():
    """
    Gibt die Wetterdaten einer Station in einem bestimmten Zeitraum zurück.
    Erwartet: station_id, start_year, end_year (Standardzeitraum: 2010-2020).
    """
    station_id = request.args.get("station_id")
    try:
        start_year = int(request.args.get("start_year", 2010))
        end_year = int(request.args.get("end_year", 2020))
    except ValueError:
        return jsonify({"error": "Ungültige Jahresangaben"}), 400

    # Existiert die Station?
    station = next((s for s in stations if s["id"] == station_id), None)
    if not station:
        return jsonify({"error": f"Station {station_id} nicht gefunden."}), 404

    # Beispieldaten für Wetterdaten (um echte Daten zu vermeiden)
    weather_data = []
    for year in range(start_year, end_year + 1):
        weather_data.append({
            "year": year,
            "annual_max": 30.0,  # Beispiel-Maximaltemperatur
            "annual_min": -5.0  # Beispiel-Minimaltemperatur
        })

    return jsonify({"station": station, "annual_data": weather_data})


@app.route("/download_weather_data", methods=["GET"])
def download_weather_data():
    """
    Simuliert den Download von Wetterdaten.
    """
    return jsonify({"message": "Wetterdaten erfolgreich heruntergeladen"}), 200


### Anwendung initialisieren ###

stations = parse_stations()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

import os
import math
import requests
import shutil
from collections import defaultdict
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from flask_cors import CORS


app = Flask(__name__)
CORS(app) 

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
    shutil.rmtree(WEATHER_DATA_DIR)
    os.makedirs(WEATHER_DATA_DIR)
    download_weather_data_for_stations(station_ids)

    return jsonify(selected_stations)

@app.route("/get_station_data", methods=["GET"])
def get_station_data():
    """Gibt die durchschnittliche TMAX und TMIN für meteorologische Jahreszeiten und das gesamte Jahr zurück."""
    station_id = request.args.get("station_id")

    try:
        start_year = int(request.args.get("start_year", 1900))
        end_year = int(request.args.get("end_year", 2100))
    except ValueError:
        return jsonify({"error": "Ungültige Jahresangaben"}), 400

    if not station_id:
        return jsonify({"error": "Station-ID fehlt"}), 400

    # ✅ Station in der Liste finden (um den Namen zu erhalten)
    station = next((s for s in stations if s["id"] == station_id), None)

    if not station:
        return jsonify({"error": "Station nicht gefunden"}), 404

    file_path = os.path.join(WEATHER_DATA_DIR, f"{station_id}.dly")
    if not os.path.exists(file_path):
        return jsonify({"error": f"Keine Wetterdaten für {station['name']} gefunden."}), 404

    # Datenstruktur für die Berechnungen
    data_by_year = defaultdict(lambda: {
        "avg_TMAX": 0, "count_TMAX": 0, 
        "avg_TMIN": 0, "count_TMIN": 0,
        "seasons": {
            "Winter": {"avg_TMAX": 0, "count_TMAX": 0, "avg_TMIN": 0, "count_TMIN": 0},
            "Spring": {"avg_TMAX": 0, "count_TMAX": 0, "avg_TMIN": 0, "count_TMIN": 0},
            "Summer": {"avg_TMAX": 0, "count_TMAX": 0, "avg_TMIN": 0, "count_TMIN": 0},
            "Autumn": {"avg_TMAX": 0, "count_TMAX": 0, "avg_TMIN": 0, "count_TMIN": 0}
        }
    })

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            element = line[17:21]  # TMAX, TMIN oder TAVG
            if element not in ["TMAX", "TMIN", "TAVG"]:
                continue  # Andere Werte ignorieren

            year = int(line[11:15])  # Jahr extrahieren
            month = int(line[15:17])  # Monat extrahieren

            # **Meteorologische Jahreszeiten zuordnen**
            if month in [12, 1, 2]:  
                season = "Winter"
                season_year = year if month != 12 else year + 1  # Dezember zählt zum nächsten Jahr
            elif month in [3, 4, 5]:  
                season = "Spring"
                season_year = year
            elif month in [6, 7, 8]:  
                season = "Summer"
                season_year = year
            elif month in [9, 10, 11]:  
                season = "Autumn"
                season_year = year

            # ❗ **Fix für Winter-Saison, die ins nächste Jahr geht**
            if season == "Winter" and season_year > end_year:
                continue  # Winter darf nicht ins nächste Jahr überlaufen

            # Nur Daten für den gewählten Zeitraum speichern
            if not (start_year <= year <= end_year):
                continue

            values = [int(line[i:i+5].strip()) for i in range(21, 261, 8) 
                      if line[i:i+5].strip() != "-9999"]  # Nur gültige Werte

            if not values:
                continue  # Falls keine Werte übrig bleiben

            # **TMAX → Durchschnitt über alle Werte berechnen**
            if element == "TMAX":
                data_by_year[year]["avg_TMAX"] += sum(values) / 10.0
                data_by_year[year]["count_TMAX"] += len(values)

                data_by_year[season_year]["seasons"][season]["avg_TMAX"] += sum(values) / 10.0
                data_by_year[season_year]["seasons"][season]["count_TMAX"] += len(values)

            # **TMIN → Durchschnitt über alle Werte berechnen**
            elif element == "TMIN":
                data_by_year[year]["avg_TMIN"] += sum(values) / 10.0
                data_by_year[year]["count_TMIN"] += len(values)

                data_by_year[season_year]["seasons"][season]["avg_TMIN"] += sum(values) / 10.0
                data_by_year[season_year]["seasons"][season]["count_TMIN"] += len(values)

            # **TAVG → Höchster Wert als TMAX, niedrigster als TMIN**
            elif element == "TAVG":
                max_value = max(values) / 10.0
                min_value = min(values) / 10.0

                data_by_year[year]["avg_TMAX"] += max_value
                data_by_year[year]["count_TMAX"] += 1

                data_by_year[year]["avg_TMIN"] += min_value
                data_by_year[year]["count_TMIN"] += 1

                data_by_year[season_year]["seasons"][season]["avg_TMAX"] += max_value
                data_by_year[season_year]["seasons"][season]["count_TMAX"] += 1

                data_by_year[season_year]["seasons"][season]["avg_TMIN"] += min_value
                data_by_year[season_year]["seasons"][season]["count_TMIN"] += 1

    # **Endgültige Berechnung der Durchschnittswerte**
    result_data = {"station": station_id, "name": station["name"], "years": {}}  # ⬅️ Name hinzugefügt

    for year, data in data_by_year.items():
        yearly_avg_TMAX = round(data["avg_TMAX"] / data["count_TMAX"], 2) if data["count_TMAX"] > 0 else None
        yearly_avg_TMIN = round(data["avg_TMIN"] / data["count_TMIN"], 2) if data["count_TMIN"] > 0 else None

        year_data = {"avg_TMAX": yearly_avg_TMAX, "avg_TMIN": yearly_avg_TMIN, "seasons": {}}

        for season, season_data in data["seasons"].items():
            avg_TMAX = round(season_data["avg_TMAX"] / season_data["count_TMAX"], 2) if season_data["count_TMAX"] > 0 else None
            avg_TMIN = round(season_data["avg_TMIN"] / season_data["count_TMIN"], 2) if season_data["count_TMIN"] > 0 else None
            if avg_TMAX is not None or avg_TMIN is not None:
                year_data["seasons"][season] = {"avg_TMAX": avg_TMAX, "avg_TMIN": avg_TMIN}

        if year_data["seasons"]:  # Nur hinzufügen, wenn es Werte gibt
            result_data["years"][year] = year_data

    return jsonify(result_data)



### 🔹 Initialisierung ###
download_station_file()
stations = parse_stations()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
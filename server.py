import os
import math
import requests
import shutil
from collections import defaultdict
from flask import Flask, request, jsonify, send_from_directory
from concurrent.futures import ThreadPoolExecutor
from flask_cors import CORS

# Flask-App initialisieren
app = Flask(__name__, static_url_path='', static_folder='.')

# CORS aktivieren
CORS(app)

# URL zur Stationsliste
STATIONS_URL = "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"

# URL für die Wetterdaten der einzelnen Stationen
BASE_WEATHER_URL = "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/all/"

# Lokaler Dateiname, unter dem die Stationsliste gespeichert wird
STATIONS_FILE = "ghcnd-stations.txt"

# Verzeichnis, in dem heruntergeladene Wetterdaten abgelegt werden
WEATHER_DATA_DIR = "ghcn_weather"


# Ordner für Wetterdaten anlegen
os.makedirs(WEATHER_DATA_DIR, exist_ok=True)

# Holt die Stationsdaten, wenn sie lokal noch nicht vorhanden sind
def download_station_file():
    if not os.path.exists(STATIONS_FILE):
        print("Stationsdatei wird geladen...")
        try:
            response = requests.get(STATIONS_URL, timeout=15)
            if response.status_code == 200:
                with open(STATIONS_FILE, "wb") as file:
                    file.write(response.content)
                print("Datei gespeichert.")
            else:
                print(f"Download fehlgeschlagen. Status: {response.status_code}")
        except Exception as e:
            print("Fehler beim Download:", e)


# Parsed die Stationsdaten (ID, Koordinaten, Name)
def parse_stations():
    stations = []

    if not os.path.exists(STATIONS_FILE):
        print(f"Datei {STATIONS_FILE} fehlt.")
        return stations

    with open(STATIONS_FILE, "r") as f:
        for line in f:
            try:
                station_id = line[0:11].strip()
                lat = float(line[12:20].strip())
                lon = float(line[21:30].strip())
                name = line[41:71].strip()

                stations.append({
                    "id": station_id,
                    "lat": lat,
                    "lon": lon,
                    "name": name
                })

            except ValueError as e:
                print(f"Fehler beim Parsen: {e}")
                continue

    return stations


# Berechnet die Entfernung zwischen zwei Koordinaten (Haversine-Formel, in km)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Holt die Wetterdaten für eine Station und speichert sie lokal ab
def download_weather_data(station_id):
    file_path = os.path.join(WEATHER_DATA_DIR, f"{station_id}.dly")

    if os.path.exists(file_path):
        print(f"{station_id}: Datei schon vorhanden.")
        return

    url = f"{BASE_WEATHER_URL}{station_id}.dly"

    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"{station_id}: Daten gespeichert.")
        else:
            print(f"{station_id}: Fehler beim Download, Status {response.status_code}")

    except Exception as e:
        print(f"{station_id}: Download fehlgeschlagen: {e}")


# Mehrere Wetterdateien gleichzeitig herunterladen
def download_weather_data_for_stations(station_ids):
    with ThreadPoolExecutor(max_workers=100) as executor:
        executor.map(download_weather_data, station_ids)

# Bei Aufruf von localhost:8080 index.html öffnen
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Prüft, ob eine Station sowohl TMAX- als auch TMIN-Daten im Start- und Endjahr hat
def has_complete_data_for_years(station_id, start_year, end_year):
    file_path = os.path.join(WEATHER_DATA_DIR, f"{station_id}.dly")
    
    if not os.path.exists(file_path):
        return False
    
    has_start_TMAX = False
    has_start_TMIN = False
    has_end_TMAX = False
    has_end_TMIN = False

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            element = line[17:21]
            year = int(line[11:15])

            if element not in ["TMAX", "TMIN"]:
                continue
            
            if year == start_year:
                values = [int(line[i:i+5].strip()) for i in range(21, 269, 8)
                          if line[i:i+5].strip() != "-9999"]
                if values:
                    if element == "TMAX":
                        has_start_TMAX = True
                    elif element == "TMIN":
                        has_start_TMIN = True

            if year == end_year:
                values = [int(line[i:i+5].strip()) for i in range(21, 269, 8)
                          if line[i:i+5].strip() != "-9999"]
                if values:
                    if element == "TMAX":
                        has_end_TMAX = True
                    elif element == "TMIN":
                        has_end_TMIN = True


            if has_start_TMAX and has_start_TMIN and has_end_TMAX and has_end_TMIN:
                return True


    return has_start_TMAX and has_start_TMIN and has_end_TMAX and has_end_TMIN


# Sucht Stationen im angegebenen Radius und filtert passende Stationen heraus
@app.route("/search_stations", methods=["GET"])
def search_stations():
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
        radius = float(request.args.get("radius", 50))
        max_results = int(request.args.get("max", 10))
        start_year = int(request.args.get("start_year", 1900))
        end_year = int(request.args.get("end_year", 2100))
    except (TypeError, ValueError):
        return jsonify({"error": "Ungültige Parameter"}), 400


    nearby_stations = [
        {**station, "distance": round(haversine(lat, lon, station["lat"], station["lon"]), 2)}
        for station in stations if haversine(lat, lon, station["lat"], station["lon"]) <= radius
    ]
    

    nearby_stations.sort(key=lambda x: x["distance"])

    station_ids = [station["id"] for station in nearby_stations]
    shutil.rmtree(WEATHER_DATA_DIR)
    os.makedirs(WEATHER_DATA_DIR)
    download_weather_data_for_stations(station_ids)


    valid_stations = []
    for station in nearby_stations:
        station_id = station["id"]
        if has_complete_data_for_years(station_id, start_year, end_year):
            valid_stations.append(station)


        if len(valid_stations) >= max_results:
            break

    return jsonify(valid_stations)



# Holt und bereitet die Daten der gefunden Stationen auf
@app.route("/get_station_data", methods=["GET"])
def get_station_data():
    station_id = request.args.get("station_id")
    try:
        start_year = int(request.args.get("start_year", 1900))
        end_year = int(request.args.get("end_year", 2100))
    except ValueError:
        return jsonify({"error": "Ungültige Jahresangaben"}), 400

    if not station_id:
        return jsonify({"error": "Station-ID fehlt"}), 400

    station = next((s for s in stations if s["id"] == station_id), None)
    if not station:
        return jsonify({"error": "Station nicht gefunden"}), 404

    file_path = os.path.join(WEATHER_DATA_DIR, f"{station_id}.dly")
    if not os.path.exists(file_path):
        return jsonify({"error": f"Keine Wetterdaten für {station['name']} gefunden."}), 404

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
            element = line[17:21]
            if element not in ["TMAX", "TMIN"]:
                continue

            year = int(line[11:15])
            month = int(line[15:17])

            if month in [12, 1, 2]:
                season = "Winter"
                season_year = year if month != 12 else year + 1
            elif month in [3, 4, 5]:
                season = "Spring"
                season_year = year
            elif month in [6, 7, 8]:
                season = "Summer"
                season_year = year
            else:
                season = "Autumn"
                season_year = year

            if not (start_year <= year <= end_year):
                continue

            skip_season = season == "Winter" and season_year > end_year

            values = [int(line[i:i+5].strip()) for i in range(21, 269, 8)
                    if line[i:i+5].strip() != "-9999"]

            if not values:
                continue

 
            if element == "TMAX":
                data_by_year[year]["avg_TMAX"] += sum(values) / 10.0
                data_by_year[year]["count_TMAX"] += len(values)

                if not skip_season:
                    data_by_year[season_year]["seasons"][season]["avg_TMAX"] += sum(values) / 10.0
                    data_by_year[season_year]["seasons"][season]["count_TMAX"] += len(values)

            elif element == "TMIN":
                data_by_year[year]["avg_TMIN"] += sum(values) / 10.0
                data_by_year[year]["count_TMIN"] += len(values)

                if not skip_season:
                    data_by_year[season_year]["seasons"][season]["avg_TMIN"] += sum(values) / 10.0
                    data_by_year[season_year]["seasons"][season]["count_TMIN"] += len(values)

    result_data = {"station": station_id, "name": station["name"], "years": {}}
    for year, data in data_by_year.items():
        if data["count_TMAX"] > 0:
            yearly_avg_TMAX = round(data["avg_TMAX"] / data["count_TMAX"], 1)
        else:
            yearly_avg_TMAX = None

        if data["count_TMIN"] > 0:
            yearly_avg_TMIN = round(data["avg_TMIN"] / data["count_TMIN"], 1)
        else:
            yearly_avg_TMIN = None

        year_data = {
            "avg_TMAX": yearly_avg_TMAX,
            "avg_TMIN": yearly_avg_TMIN,
            "seasons": {},
        }

        for season, season_data in data["seasons"].items():
            if season_data["count_TMAX"] > 0:
                avg_TMAX = round(season_data["avg_TMAX"] / season_data["count_TMAX"], 1)
            else:
                avg_TMAX = None
            if season_data["count_TMIN"] > 0:
                avg_TMIN = round(season_data["avg_TMIN"] / season_data["count_TMIN"], 1)
            else:
                avg_TMIN = None
            if avg_TMAX is not None or avg_TMIN is not None:
                year_data["seasons"][season] = {"avg_TMAX": avg_TMAX, "avg_TMIN": avg_TMIN}

        if year_data["seasons"]:
            result_data["years"][year] = year_data

    return jsonify(result_data)

# Initialisierung
download_station_file()
stations = parse_stations()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

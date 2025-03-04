import os
import math
import random
import requests
import gzip
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup

app = Flask(__name__)

STATIONS_URL = "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"
STATIONS_FILE = "ghcnd-stations.txt"
WEATHER_DATA_DIR = "weather_data"


### Hilfsfunktionen ###

def download_station_file():
    """Lädt die Stationsdatei herunter, falls sie nicht existiert."""
    if not os.path.exists(STATIONS_FILE):
        print("Stationsdatei wird heruntergeladen...")
        response = requests.get(STATIONS_URL)
        if response.status_code == 200:
            with open(STATIONS_FILE, "wb") as file:
                file.write(response.content)
            print("Download erfolgreich.")
        else:
            print("Fehler beim Herunterladen der Stationsdatei:", response.status_code)


def parse_stations():
    """
    Parst die heruntergeladene Stationsdatei und liefert eine Liste von Stationen zurück.
    Jede Station ist ein Dictionary mit ID, Lat, Lon und Name.
    """
    stations = []
    if not os.path.exists(STATIONS_FILE):
        print(f"Stationsdatei {STATIONS_FILE} wurde nicht gefunden.")
        return stations

    with open(STATIONS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                # NOAA-Format (fixe Spaltenbreiten)
                station_id = line[0:11].strip()
                lat = float(line[12:20].strip())
                lon = float(line[21:30].strip())
                station_name = line[41:71].strip()
                stations.append({"id": station_id, "lat": lat, "lon": lon, "name": station_name})
            except ValueError:
                continue
    return stations


def download_all_weather_data():
    """
    Lädt die täglichen Wetterdaten von der NOAA-Website herunter und speichert sie im Ordner 'weather_data'.
    """
    base_url = "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/"
    response = requests.get(base_url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        # Alle Links auf der Seite durchsuchen
        links = soup.find_all("a", href=True)

        # Ordner erstellen, um die Daten zu speichern
        if not os.path.exists(WEATHER_DATA_DIR):
            os.makedirs(WEATHER_DATA_DIR)

        for link in links:
            file_name = link["href"]
            if file_name.endswith(".gz"):  # Nur .gz-Dateien herunterladen
                file_url = base_url + file_name
                print(f"Lade Datei herunter: {file_name}")

                file_response = requests.get(file_url)
                if file_response.status_code == 200:
                    with open(f"{WEATHER_DATA_DIR}/{file_name}", "wb") as file:
                        file.write(file_response.content)
                    print(f"Datei {file_name} erfolgreich heruntergeladen.")
                else:
                    print(f"Fehler beim Herunterladen der Datei {file_name}: {file_response.status_code}")
    else:
        print("Fehler beim Abrufen der Website:", response.status_code)


def haversine(lat1, lon1, lat2, lon2):
    """Berechnet die Entfernung zwischen zwei Punkten auf der Erde in Kilometern."""
    R = 6371  # Erdradius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


### Endpunkte der Flask-API ###

@app.route("/search_stations", methods=["GET"])
def search_stations():
    """
    Sucht Stationen anhand geographischer Koordinaten, Suchradius und maximaler Anzahl.
    Erwartete Query-Parameter:
      - lat: Breite
      - lon: Länge
      - radius: Radius in Kilometern (Standard 50 km)
      - max: Maximale Anzahl (Standard 10)
    """
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
    return jsonify(nearby_stations[:max_results])


@app.route("/get_station_data", methods=["GET"])
def get_station_data():
    """
    Gibt tatsächliche Wetterdaten aus den heruntergeladenen GHCN-Daten zurück.
    Erwartete Query-Parameter:
      - station_id: ID der Station
      - start_year: Startjahr (Standard 2010)
      - end_year: Endjahr (Standard 2020)
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

    # Wetterdaten aus den GHCN-Daten (.gz-Dateien) extrahieren
    weather_data = []  # Liste für aufbereitete Wetterdaten
    for year in range(start_year, end_year + 1):
        file_path = os.path.join(WEATHER_DATA_DIR, f"{year}.csv.gz")
        if not os.path.exists(file_path):
            continue  # Überspringen, wenn die Datei für das Jahr nicht existiert

        with gzip.open(file_path, mode="rt", encoding="utf-8") as file:
            for line in file:
                # Zeilenverarbeitung nach GHCN-Datenschema
                if line.startswith(station_id):  # Nur Daten dieser Station
                    parts = line.split()
                    date = parts[1]  # Datum im Format YYYYMMDD
                    element = parts[2]  # Element-Typ (z.B. TMAX, TMIN, PRCP)
                    value = int(parts[3]) / 10  # Wert (Skalierung, z.B. in °C)

                    # Strukturierte Wetterdaten speichern (Gefiltert auf Element)
                    weather_data.append({"date": date, "element": element, "value": value})

    if not weather_data:
        return jsonify({"error": "Keine Wetterdaten für den angegebenen Zeitraum gefunden"}), 404

    # Die Wetterdaten nach Jahr und Element gruppieren
    annual_data = {}
    for entry in weather_data:
        year = int(entry["date"][:4])  # Jahr aus dem Datum extrahieren
        if entry["element"] in ["TMAX", "TMIN"]:  # Nur Temperaturdaten berücksichtigen
            if year not in annual_data:
                annual_data[year] = {"TMAX": [], "TMIN": []}
            annual_data[year][entry["element"]].append(entry["value"])

    # Ergebnisse aggregieren (Mittelwerte berechnen)
    aggregated_data = []
    for year, elements in annual_data.items():
        tmax_avg = round(sum(elements["TMAX"]) / len(elements["TMAX"]), 1) if elements["TMAX"] else None
        tmin_avg = round(sum(elements["TMIN"]) / len(elements["TMIN"]), 1) if elements["TMIN"] else None
        aggregated_data.append({"year": year, "annual_max": tmax_avg, "annual_min": tmin_avg})

    # Daten sortieren
    aggregated_data.sort(key=lambda x: x["year"])

    return jsonify({"station": station, "annual_data": aggregated_data})



@app.route("/download_weather_data", methods=["GET"])
def download_weather_data():
    """
    Lädt alle täglichen Wetterdaten herunter und speichert sie in einem lokalen Ordner.
    """
    try:
        download_all_weather_data()
        return jsonify({"message": "Wetterdaten erfolgreich heruntergeladen"}), 200
    except Exception as e:
        return jsonify({"error": f"Fehler beim Herunterladen der Wetterdaten: {str(e)}"}), 500


### Initialisierung ###
download_station_file()
stations = parse_stations()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

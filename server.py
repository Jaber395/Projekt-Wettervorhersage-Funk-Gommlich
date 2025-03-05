import os
import math
import gzip
from flask import Flask, request, jsonify

app = Flask(__name__)

# URLs und Pfade
STATIONS_URL = "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"
BASE_WEATHER_URL = "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/all"
STATIONS_FILE = "ghcnd-stations.txt"
WEATHER_DATA_DIR = "weather_data"

stations = []


### Hilfsfunktionen ###

def download_station_file():
    """Lädt die Stationsdatei herunter, falls sie nicht vorhanden ist."""
    if not os.path.exists(STATIONS_FILE):
        print("Stationsdatei wird heruntergeladen...")
        response = requests.get(STATIONS_URL)
        if response.status_code == 200:
            with open(STATIONS_FILE, "wb") as file:
                file.write(response.content)
            print("Download erfolgreich.")
        else:
            raise Exception(f"Fehler beim Herunterladen der Stationsdatei: {response.status_code}")


def parse_stations():
    """
    Liest die Stationsdatei und gibt eine Liste von Stationen zurück (als Dictionary).
    """
    parsed_stations = []
    if not os.path.exists(STATIONS_FILE):
        print(f"Die Datei {STATIONS_FILE} ist nicht vorhanden.")
        return parsed_stations

    with open(STATIONS_FILE, "r", encoding="utf-8") as file:
        for line in file:
            try:
                station_id = line[0:11].strip()
                lat = float(line[12:20].strip())
                lon = float(line[21:30].strip())
                station_name = line[41:71].strip()
                parsed_stations.append({"id": station_id, "lat": lat, "lon": lon, "name": station_name})
            except ValueError:
                continue  # Fehlerhafte Zeilen überspringen
    return parsed_stations


def haversine(lat1, lon1, lat2, lon2):
    """Berechnet die Entfernung zwischen zwei Punkten auf der Erde in Kilometern."""
    R = 6371  # Erdradius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def download_weather_data_for_stations(station_ids):
    """Lädt die Wetterdaten für eine Liste von Stationen herunter und speichert sie in `WEATHER_DATA_DIR`."""
    if not os.path.exists(WEATHER_DATA_DIR):
        os.makedirs(WEATHER_DATA_DIR)

    for station_id in station_ids:
        file_url = f"{BASE_WEATHER_URL}/{station_id}.dly"
        target_path = os.path.join(WEATHER_DATA_DIR, f"{station_id}.gz")

        print(f"DEBUG: Versuche herunterzuladen: {file_url}")  # Neue Debug-Ausgabe

        # Datei nur herunterladen, wenn sie nicht vorhanden ist
        if not os.path.exists(target_path):
            print(f"Lade Daten für Station {station_id} herunter...")
            response = requests.get(file_url)
            if response.status_code == 200:
                with open(target_path, "wb") as file:
                    file.write(response.content)
                print(f"Download von {station_id} erfolgreich.")
                # **Überprüfung, ob die Datei nicht leer ist**
                if os.path.exists(target_path):
                    if os.path.getsize(target_path) == 0:
                        print(f"Fehler: Die Datei {target_path} ist leer.")

            else:
                print(f"Fehler beim Herunterladen von {station_id}: {response.status_code}")


def process_weather_data_for_station(station_id):
    """
    Verarbeitet die Wetterdaten für eine spezifische Station.

    - Filtert nur die Datenelemente "TMAX" und "TMIN".
    - Schließt fehlerhafte Werte (-9999) aus.
    - Skaliert Temperaturwerte (Werte werden durch 10 geteilt).

    :param station_id: Die ID der Wetterstation.
    :return: Eine Liste von Temperaturdaten oder eine Fehlermeldung.
    """
    station_data_path = os.path.join(WEATHER_DATA_DIR, f"{station_id}.gz")

    # Prüfe, ob die Daten-Datei vorhanden ist
    if not os.path.exists(station_data_path):
        print(f"Fehler: Wetterdaten für Station {station_id} nicht gefunden ({station_data_path})")
        return None, f"Keine Wetterdaten für Station {station_id} gefunden."

    temperatures = []

    # Öffne die .gz-Datei und verarbeite jede Zeile
    try:
        with gzip.open(station_data_path, "rt", encoding="utf-8") as file:
            for line in file:
                try:
                    # NOAA-Format: Spalten extrahieren
                    current_station_id = line[0:11].strip()  # Station ID (Spalten 0-10)
                    if current_station_id != station_id:
                        continue  # Überspringen, wenn die Station-ID nicht übereinstimmt

                    date = line[11:19].strip()  # Datum (YYYYMMDD, Spalten 11-18)
                    element = line[17:21].strip()  # TMAX oder TMIN (Spalten 17-21)
                    value = int(line[21:26].strip())  # Temperaturwert (Spalten 21-26)

                    # Filtere nur "TMAX" und "TMIN"
                    if element not in ["TMAX", "TMIN"]:
                        continue

                    # Fehlerhafte Werte (-9999) ausschließen
                    if value == -9999:
                        continue

                    # Temperaturwert skalieren (Wert / 10)
                    temperature = value / 10.0

                    # Ergebnis speichern
                    temperatures.append({
                        "date": date,
                        "type": element,
                        "temperature": temperature
                    })

                except ValueError as e:
                    # Fehlerhafte Zeilen überspringen und debuggen
                    print(f"Fehler beim Verarbeiten einer Zeile in {station_id}: {e}")
                    continue

    except FileNotFoundError:
        print(f"Fehler: Datei {station_data_path} nicht gefunden.")
        return None, f"Datei für Station {station_id} fehlt."
    except gzip.BadGzipFile:
        print(f"Fehler: Ungültige .gz-Datei für Station {station_id}.")
        return None, f"Ungültige Datei für Station {station_id}."
    except Exception as e:
        print(f"Unerwarteter Fehler beim Verarbeiten der Wetterdaten von {station_id}: {e}")
        return None, f"Fehler beim Verarbeiten der Datei für Station {station_id}."

    # Ergebnisvalidierung
    if not temperatures:
        print(f"Keine gültigen Temperaturdaten für Station {station_id}")
        return None, f"Keine gültigen Temperaturdaten für Station {station_id} gefunden."

    print(f"Erfolgreich {len(temperatures)} Datensätze für Station {station_id} verarbeitet.")
    return temperatures, None


### API-Endpunkte ###

@app.route("/search_stations", methods=["GET"])
def search_stations():
    """
    Sucht Stationen nach Koordinaten und Radius.
    """
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
        radius = float(request.args.get("radius", 50))
        max_results = int(request.args.get("max", 10))
    except (TypeError, ValueError):
        return jsonify({"error": "Ungültige Parameter"}), 400

    results = []
    for station in stations:
        distance = haversine(lat, lon, station["lat"], station["lon"])
        if distance <= radius:
            station_copy = station.copy()
            station_copy["distance"] = round(distance, 2)
            results.append(station_copy)

    results.sort(key=lambda x: x["distance"])
    return jsonify(results[:max_results])


@app.route("/get_station_data", methods=["GET"])
def get_station_data():
    """
    Gibt die Wetterdaten einer Station basierend auf ihrer ID und einem Zeitraum zurück.
    """
    station_id = request.args.get("station_id")
    try:
        start_year = int(request.args.get("start_year", 2010))
        end_year = int(request.args.get("end_year", 2020))
    except ValueError:
        return jsonify({"error": "Ungültige Jahresangaben"}), 400

    # Station prüfen
    station = next((s for s in stations if s["id"] == station_id), None)
    if not station:
        return jsonify({"error": f"Station {station_id} nicht gefunden."}), 404

    # Wetterdaten verarbeiten
    temperatures, error = process_weather_data_for_station(station_id)
    if error:
        return jsonify({"error": error}), 404

    # Filtere Daten nach Zeitraum
    filtered_temperatures = [
        temp for temp in temperatures
        if start_year <= int(temp["date"][:4]) <= end_year
    ]

    if not filtered_temperatures:
        return jsonify({"error": f"Keine Temperaturdaten für den Zeitraum {start_year}-{end_year} gefunden."}), 404

    return jsonify({
        "station": station,
        "temperatures": filtered_temperatures
    })


@app.route("/download_weather_data", methods=["GET"])
def download_weather_data():
    """
    Lädt Wetterdaten für alle Stationen herunter.
    """
    station_ids = [station["id"] for station in stations]
    download_weather_data_for_stations(station_ids)
    return jsonify({"message": "Wetterdaten erfolgreich heruntergeladen."}), 200


### Initialisierung ###

stations = parse_stations()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

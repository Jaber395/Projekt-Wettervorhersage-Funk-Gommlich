import os
import math
import gzip
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# URLs and paths
STATIONS_URL = "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"
BASE_WEATHER_URL = "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/all"
STATIONS_FILE = "ghcnd-stations.txt"
WEATHER_DATA_DIR = "weather_data"

stations = []


### Helper functions ###

def download_station_file():
    """Downloads the station file if it doesn't exist."""
    if not os.path.exists(STATIONS_FILE):
        print("Downloading station file...")
        response = requests.get(STATIONS_URL)
        if response.status_code == 200:
            with open(STATIONS_FILE, "wb") as file:
                file.write(response.content)
            print("Download successful.")
        else:
            raise Exception(f"Error downloading station file: {response.status_code}")


def parse_stations():
    """
    Reads the station file and returns a list of stations (as dictionaries).
    """
    parsed_stations = []
    if not os.path.exists(STATIONS_FILE):
        print(f"File {STATIONS_FILE} does not exist.")
        download_station_file()

    with open(STATIONS_FILE, "r", encoding="utf-8") as file:
        for line in file:
            try:
                station_id = line[0:11].strip()
                lat = float(line[12:20].strip())
                lon = float(line[21:30].strip())
                # Extraktion des vollständigen Stationsnamens (war: station_name = line[41:71].strip())
                parts = line[36:].strip().rsplit(maxsplit=2)  # Splittet nur die letzten beiden Werte (Bundesstaat, Land)
                station_name = " ".join(parts[:-2])  # Alles außer den letzten beiden Teilen ist der Name
                parsed_stations.append({"id": station_id, "lat": lat, "lon": lon, "name": station_name})
            except ValueError:
                continue  # Skip faulty lines
    return parsed_stations


def haversine(lat1, lon1, lat2, lon2):
    """Calculates the distance between two points on Earth in kilometers."""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def download_weather_data_for_stations(station_ids):
    """Downloads weather data for a list of stations and saves it to `WEATHER_DATA_DIR`."""
    if not os.path.exists(WEATHER_DATA_DIR):
        os.makedirs(WEATHER_DATA_DIR)

    for station_id in station_ids:
        file_url = f"{BASE_WEATHER_URL}/{station_id}.dly"
        target_path = os.path.join(WEATHER_DATA_DIR, f"{station_id}.gz")

        # Only download if file doesn't exist
        if not os.path.exists(target_path):
            print(f"Downloading data for station {station_id}...")
            response = requests.get(file_url)
            if response.status_code == 200:
                # Compress the downloaded data and save as .gz
                with gzip.open(target_path, "wb") as gz_file:
                    gz_file.write(response.content)
                print(f"Download for {station_id} successful.")

                # Check if file is not empty
                if os.path.getsize(target_path) == 0:
                    print(f"Error: File {target_path} is empty.")
            else:
                print(f"Error downloading {station_id}: {response.status_code}")


def process_weather_data_for_station(station_id):
    """
    Processes weather data for a specific station:
    - Filters only for TMAX and TMIN elements
    - Excludes invalid values (-9999)
    - Scales temperature values (dividing by 10)

    Args:
        station_id: The ID of the weather station

    Returns:
        tuple: (temperatures_list, error_message)
    """
    station_data_path = os.path.join(WEATHER_DATA_DIR, f"{station_id}.gz")

    # Check if data file exists
    if not os.path.exists(station_data_path):
        print(f"Error: Weather data for station {station_id} not found ({station_data_path})")
        return None, f"No weather data found for station {station_id}."

    temperatures = []

    try:
        with gzip.open(station_data_path, "rt", encoding="utf-8") as file:
            for line in file:
                try:
                    # Parse NOAA format columns
                    current_station_id = line[0:11].strip()
                    year = line[11:15].strip()
                    month = line[15:17].strip()
                    element = line[17:21].strip()

                    # Skip if not TMAX or TMIN
                    if element not in ["TMAX", "TMIN"]:
                        continue

                    # Process daily values (each line contains a month of data)
                    # Each daily value uses 8 characters (5 for value, 3 for flags)
                    # Starting at position 21
                    for day in range(1, 32):
                        pos = 21 + (day - 1) * 8
                        if pos + 5 > len(line):
                            break

                        try:
                            value_str = line[pos:pos + 5].strip()
                            if not value_str:
                                continue

                            value = int(value_str)

                            # Skip invalid values
                            if value == -9999:
                                continue

                            # Scale temperature (divide by 10)
                            temperature = value / 10.0

                            # Format date as YYYYMMDD
                            date = f"{year}{month}{day:02d}"

                            temperatures.append({
                                "date": date,
                                "type": element,
                                "temperature": temperature
                            })
                        except ValueError:
                            continue

                except Exception as e:
                    print(f"Error processing line for station {station_id}: {e}")
                    continue

    except FileNotFoundError:
        return None, f"File for station {station_id} not found."
    except gzip.BadGzipFile:
        return None, f"Invalid gzip file for station {station_id}."
    except Exception as e:
        return None, f"Error processing file for station {station_id}: {str(e)}"

    if not temperatures:
        return None, f"No valid temperature data found for station {station_id}."

    print(f"Successfully processed {len(temperatures)} records for station {station_id}.")
    return temperatures, None


### API endpoints ###

@app.route("/search_stations", methods=["GET"])
def search_stations():
    """
    Searches for stations by coordinates and radius.
    """
    # Initialize stations if not already done
    global stations
    if not stations:
        stations = parse_stations()
        print(f"Loaded {len(stations)} stations.")

    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
        radius = float(request.args.get("radius", 50))
        max_results = int(request.args.get("max", 10))
    except (TypeError, ValueError):
        return jsonify({"error": "Ungültige Parameter"}), 400  # Fehlermeldung geändert

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
    Returns weather data for a station based on its ID and a time period.
    """
    # Initialize stations if not already done
    global stations
    if not stations:
        stations = parse_stations()
        print(f"Loaded {len(stations)} stations.")

    station_id = request.args.get("station_id")
    if not station_id:
        return jsonify({"error": "Keine Station-ID angegeben"}), 400  # Fehlermeldung geändert

    try:
        start_year = int(request.args.get("start_year", 2010))
        end_year = int(request.args.get("end_year", 2020))
    except ValueError:
        return jsonify({"error": "Ungültige Jahresangaben"}), 400  # Fehlermeldung geändert

    # Check station
    station = next((s for s in stations if s["id"] == station_id), None)
    if not station:
        return jsonify({"error": "Station nicht gefunden"}), 404  # Fehlermeldung geändert

    # Check if weather data exists, if not download it
    station_data_path = os.path.join(WEATHER_DATA_DIR, f"{station_id}.gz")
    if not os.path.exists(station_data_path):
        download_weather_data_for_stations([station_id])

    # Process weather data
    temperatures, error = process_weather_data_for_station(station_id)
    if error:
        return jsonify({"error": error}), 404

    # Filter data by time period
    filtered_temperatures = [
        temp for temp in temperatures
        if start_year <= int(temp["date"][:4]) <= end_year
    ]

    if not filtered_temperatures:
        return jsonify({"error": f"Keine Temperaturdaten für den Zeitraum {start_year}-{end_year} gefunden."}), 404  # Fehlermeldung geändert

    # Rückgabeformat angepasst an test_get_station_data_valid
    return jsonify({
        "id": station_id,
        "name": station["name"],
        "lat": station["lat"],
        "lon": station["lon"],
        "temperatures": filtered_temperatures
    })


@app.route("/download_weather_data", methods=["GET"])
def download_weather_data_endpoint():
    """
    Downloads weather data for all stations.
    """
    # Initialize stations if not already done
    global stations
    if not stations:
        stations = parse_stations()
        print(f"Loaded {len(stations)} stations.")

    station_id = request.args.get("station_id")
    if station_id:
        # Download data for a specific station
        download_weather_data_for_stations([station_id])
        return jsonify({"message": f"Wetterdaten für Station {station_id} erfolgreich heruntergeladen."}), 200  # Fehlermeldung geändert
    else:
        # Download data for all stations (could be a lot!)
        station_ids = [station["id"] for station in stations]
        download_weather_data_for_stations(station_ids)
        return jsonify({"message": "Wetterdaten für alle Stationen erfolgreich heruntergeladen."}), 200  # Fehlermeldung geändert


@app.route("/process_weather_data", methods=["GET"])
def process_weather_data_endpoint():
    """
    Processes weather data for a specific station and returns the results.
    """
    # Initialize stations if not already done
    global stations
    if not stations:
        stations = parse_stations()
        print(f"Loaded {len(stations)} stations.")

    station_id = request.args.get("station_id")
    if not station_id:
        return jsonify({"error": "Keine Station-ID angegeben"}), 400  # Fehlermeldung geändert

    # Check if weather data exists, if not download it
    station_data_path = os.path.join(WEATHER_DATA_DIR, f"{station_id}.gz")
    if not os.path.exists(station_data_path):
        download_weather_data_for_stations([station_id])

    temperatures, error = process_weather_data_for_station(station_id)
    if error:
        return jsonify({"error": error}), 404

    return jsonify({
        "station_id": station_id,
        "temperatures": temperatures
    })


# Initialize when imported
if stations == []:
    if not os.path.exists(STATIONS_FILE):
        download_station_file()
    stations = parse_stations()
    print(f"Loaded {len(stations)} stations.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

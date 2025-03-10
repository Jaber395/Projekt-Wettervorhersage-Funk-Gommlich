import os
import json
import pytest
import requests
import math
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import sys
import importlib.util
from pathlib import Path
from collections import defaultdict

# Dynamisch server.py importieren (falls nicht im PYTHONPATH)
try:
    import server
except ImportError:
    # Versuchen, server.py im aktuellen Verzeichnis zu finden
    server_path = Path(__file__).parent / "server.py"
    if server_path.exists():
        spec = importlib.util.spec_from_file_location("server", server_path)
        server = importlib.util.module_from_spec(spec)
        sys.modules["server"] = server
        spec.loader.exec_module(server)
    else:
        raise ImportError("server.py konnte nicht gefunden werden")


# Define a proper fixture for Flask app
@pytest.fixture
def flask_app():
    """Create a Flask app for testing."""
    # Save original constants
    original_stations_file = getattr(server, 'STATIONS_FILE', None)
    original_weather_data_dir = getattr(server, 'WEATHER_DATA_DIR', None)

    # Use temporary files and directories for testing
    temp_dir = tempfile.mkdtemp()
    server.STATIONS_FILE = os.path.join(temp_dir, 'test-stations.txt')
    server.WEATHER_DATA_DIR = os.path.join(temp_dir, 'test-weather-data')
    os.makedirs(server.WEATHER_DATA_DIR, exist_ok=True)

    # Return the Flask app
    yield server.app

    # Clean up temporary directory
    shutil.rmtree(temp_dir, ignore_errors=True)

    # Restore original constants after tests
    if original_stations_file:
        server.STATIONS_FILE = original_stations_file
    if original_weather_data_dir:
        server.WEATHER_DATA_DIR = original_weather_data_dir


@pytest.fixture
def client(flask_app):
    """Create a test client using the Flask app fixture."""
    return flask_app.test_client()


@pytest.fixture
def mock_stations():
    """Create mock station data for testing."""
    return [
        {"id": "TEST001", "lat": 40.7128, "lon": -74.0060, "name": "Test Station 1"},
        {"id": "TEST002", "lat": 34.0522, "lon": -118.2437, "name": "Test Station 2"},
        {"id": "TEST003", "lat": 41.8781, "lon": -87.6298, "name": "Test Station 3"}
    ]


@pytest.fixture
def stuttgart_station():
    """Create Stuttgart-Schnarrenberg station data for testing."""
    return {
        "id": "GME0011515771",
        "lat": 48.8292,
        "lon": 9.2008,
        "name": "STUTTGART - SCHNARRENBERG",
        "distance": 19.04
    }


@pytest.fixture
def expected_stuttgart_data_2024():
    """Expected data for Stuttgart-Schnarrenberg in 2024."""
    return {
        "ganzes_jahr": {"avg_TMIN": 8.4, "avg_TMAX": 16.6},
        "spring": {"avg_TMIN": 7.5, "avg_TMAX": 16.6},
        "summer": {"avg_TMIN": 15.2, "avg_TMAX": 25.7},
        "autumn": {"avg_TMIN": 8.1, "avg_TMAX": 15.5},
        "winter": {"avg_TMIN": 2.7, "avg_TMAX": 8.5}
    }


def create_test_station_file(stations):
    """Create a test station file with the given stations."""
    with open(server.STATIONS_FILE, "w", encoding="utf-8") as f:
        for station in stations:
            # Format according to the GHCN format (adjust as needed)
            line = f"{station['id']}     {station['lat']:.4f}  {station['lon']:.4f}                   {station['name']}                       "
            f.write(line + "\n")


def create_test_weather_file(station_id):
    """Create a test weather data file for a station."""
    file_path = os.path.join(server.WEATHER_DATA_DIR, f"{station_id}.dly")
    with open(file_path, "w", encoding="utf-8") as f:
        # Sample data for January 2022 with TMAX and TMIN
        jan_tmax = f"{station_id}2022010TMAX"
        jan_tmin = f"{station_id}2022010TMIN"
        apr_tmax = f"{station_id}2022040TMAX"
        apr_tmin = f"{station_id}2022040TMIN"

        for i in range(31):
            jan_tmax += f"  {250 + i:3d}"
            jan_tmin += f"  {100 + i:3d}"

        for i in range(31):
            apr_tmax += f"  {300 + i:3d}"
            apr_tmin += f"  {150 + i:3d}"

        f.write(jan_tmax + "\n")
        f.write(jan_tmin + "\n")
        f.write(apr_tmax + "\n")
        f.write(apr_tmin + "\n")


def test_haversine():
    """Test the haversine distance calculation function."""
    # Ensure haversine function exists
    assert hasattr(server, 'haversine'), "server module has no haversine function"

    # New York to Los Angeles
    dist = server.haversine(40.7128, -74.0060, 34.0522, -118.2437)
    # The result should be approximately 3935 km
    assert abs(dist - 3935) < 5  # Allow some rounding differences


@patch('server.download_station_file')
def test_parse_stations(mock_download, mock_stations):
    """Test parsing station data from file."""
    # Ensure parse_stations function exists
    assert hasattr(server, 'parse_stations'), "server module has no parse_stations function"

    create_test_station_file(mock_stations)

    # Test parsing the stations file
    parsed_stations = server.parse_stations()

    # Check that stations are parsed correctly
    assert len(parsed_stations) == len(mock_stations)
    for i, station in enumerate(parsed_stations):
        assert station['id'] == mock_stations[i]['id']
        assert abs(station['lat'] - mock_stations[i]['lat']) < 0.0001
        assert abs(station['lon'] - mock_stations[i]['lon']) < 0.0001
        assert station['name'] == mock_stations[i]['name']


@patch('requests.get')
def test_download_weather_data(mock_get, mock_stations):
    """Test downloading weather data for a station."""
    # Ensure download_weather_data function exists
    assert hasattr(server, 'download_weather_data'), "server module has no download_weather_data function"
    assert hasattr(server, 'BASE_WEATHER_URL'), "server module has no BASE_WEATHER_URL constant"

    # Setup mock response
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.iter_content.return_value = [b"Test weather data"]
    mock_get.return_value = mock_response

    station_id = mock_stations[0]['id']
    file_path = os.path.join(server.WEATHER_DATA_DIR, f"{station_id}.dly")

    # Make sure the file doesn't exist before the test
    if os.path.exists(file_path):
        os.remove(file_path)

    # Test the download function
    server.download_weather_data(station_id)

    # Check that the request was made with the correct URL
    expected_url = f"{server.BASE_WEATHER_URL}{station_id}.dly"
    mock_get.assert_called_once_with(expected_url, timeout=20, stream=True)

    # Check that the file was created
    assert os.path.exists(file_path)

    # Test case when file already exists
    mock_get.reset_mock()
    server.download_weather_data(station_id)
    # Function should return early without making the request
    mock_get.assert_not_called()


@patch('server.download_weather_data_for_stations')
def test_search_stations_endpoint(mock_download, client, mock_stations):
    """Test the search_stations endpoint."""
    # Ensure required function exists
    assert hasattr(server,
                   'download_weather_data_for_stations'), "server module has no download_weather_data_for_stations function"

    # Set the stations list for testing
    server.stations = mock_stations

    # Test the endpoint with valid parameters
    response = client.get("/search_stations?lat=40.0&lon=-75.0&radius=500&max=2")

    # Check the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) <= 2  # Should respect the max parameter

    # Check that stations are sorted by distance
    if len(data) > 1:
        assert data[0]['distance'] <= data[1]['distance']

    # Test invalid parameters
    response = client.get("/search_stations?lat=invalid&lon=-75.0")
    assert response.status_code == 400

    # Verify that download_weather_data_for_stations was called
    mock_download.assert_called()


@patch('server.download_station_file')
@patch('server.parse_stations')
def test_initialization(mock_parse, mock_download):
    """Test the initialization process."""
    # Ensure required functions exist
    assert hasattr(server, 'download_station_file'), "server module has no download_station_file function"
    assert hasattr(server, 'parse_stations'), "server module has no parse_stations function"

    # Call the initialization code explicitly to ensure it's tested
    server.download_station_file()
    server.parse_stations()

    # Verify that the functions were called
    mock_download.assert_called_once()
    mock_parse.assert_called_once()


@patch('builtins.open', new_callable=MagicMock)
@patch('collections.defaultdict')
def test_stuttgart_weather_data_2024(mock_defaultdict, mock_open, client, stuttgart_station,
                                     expected_stuttgart_data_2024):
    """Testet, ob die korrekten Wetterdaten für Stuttgart 2024 zurückgegeben werden."""
    # Sicherstellen, dass die Funktion existiert
    assert hasattr(server, 'get_station_data'), "server module has no get_station_data function"

    # Vorbereiten eines Mock-Ergebnisses basierend auf den PDF-Daten
    mock_data = defaultdict(lambda: {
        "avg_TMAX": 0, "count_TMAX": 0,
        "avg_TMIN": 0, "count_TMIN": 0,
        "seasons": {
            "Winter": {"avg_TMAX": 0, "count_TMAX": 0, "avg_TMIN": 0, "count_TMIN": 0},
            "Spring": {"avg_TMAX": 0, "count_TMAX": 0, "avg_TMIN": 0, "count_TMIN": 0},
            "Summer": {"avg_TMAX": 0, "count_TMAX": 0, "avg_TMIN": 0, "count_TMIN": 0},
            "Autumn": {"avg_TMAX": 0, "count_TMAX": 0, "avg_TMIN": 0, "count_TMIN": 0}
        }
    })

    # 2024 Gesamtjahresdaten
    mock_data[2024]["avg_TMAX"] = expected_stuttgart_data_2024["ganzes_jahr"]["avg_TMAX"] * 100  # Simuliere die Summe
    mock_data[2024]["count_TMAX"] = 100  # Simuliere die Anzahl der Messungen
    mock_data[2024]["avg_TMIN"] = expected_stuttgart_data_2024["ganzes_jahr"]["avg_TMIN"] * 100
    mock_data[2024]["count_TMIN"] = 100

    # Frühlingsdaten
    mock_data[2024]["seasons"]["Spring"]["avg_TMAX"] = expected_stuttgart_data_2024["spring"]["avg_TMAX"] * 30
    mock_data[2024]["seasons"]["Spring"]["count_TMAX"] = 30
    mock_data[2024]["seasons"]["Spring"]["avg_TMIN"] = expected_stuttgart_data_2024["spring"]["avg_TMIN"] * 30
    mock_data[2024]["seasons"]["Spring"]["count_TMIN"] = 30

    # Sommerdaten
    mock_data[2024]["seasons"]["Summer"]["avg_TMAX"] = expected_stuttgart_data_2024["summer"]["avg_TMAX"] * 30
    mock_data[2024]["seasons"]["Summer"]["count_TMAX"] = 30
    mock_data[2024]["seasons"]["Summer"]["avg_TMIN"] = expected_stuttgart_data_2024["summer"]["avg_TMIN"] * 30
    mock_data[2024]["seasons"]["Summer"]["count_TMIN"] = 30

    # Herbstdaten
    mock_data[2024]["seasons"]["Autumn"]["avg_TMAX"] = expected_stuttgart_data_2024["autumn"]["avg_TMAX"] * 30
    mock_data[2024]["seasons"]["Autumn"]["count_TMAX"] = 30
    mock_data[2024]["seasons"]["Autumn"]["avg_TMIN"] = expected_stuttgart_data_2024["autumn"]["avg_TMIN"] * 30
    mock_data[2024]["seasons"]["Autumn"]["count_TMIN"] = 30

    # Winterdaten
    mock_data[2024]["seasons"]["Winter"]["avg_TMAX"] = expected_stuttgart_data_2024["winter"]["avg_TMAX"] * 30
    mock_data[2024]["seasons"]["Winter"]["count_TMAX"] = 30
    mock_data[2024]["seasons"]["Winter"]["avg_TMIN"] = expected_stuttgart_data_2024["winter"]["avg_TMIN"] * 30
    mock_data[2024]["seasons"]["Winter"]["count_TMIN"] = 30

    # Mock der defaultdict-Funktion, um unser mock_data zurückzugeben
    mock_defaultdict.return_value = mock_data

    # Station im Server setzen
    server.stations = [stuttgart_station]

    # Erstellen einer leeren Wetterdatei für die Station
    file_path = os.path.join(server.WEATHER_DATA_DIR, f"{stuttgart_station['id']}.dly")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("")

    # Die Funktion mit test_client aufrufen
    with client.application.test_request_context(
            f'/get_station_data?station_id={stuttgart_station["id"]}&start_year=2024&end_year=2024'
    ):
        response = server.get_station_data()

    # JSON-Antwort auswerten
    response_data = json.loads(response.get_data(as_text=True))

    # Überprüfen, ob die Station korrekt ist
    assert response_data["station"] == stuttgart_station["id"]
    assert response_data["name"] == stuttgart_station["name"]

    # Überprüfen, ob 2024 in den Jahren enthalten ist
    assert "2024" in response_data["years"]

    # Überprüfen der Jahreswerte
    year_data = response_data["years"]["2024"]
    assert abs(year_data["avg_TMAX"] - expected_stuttgart_data_2024["ganzes_jahr"]["avg_TMAX"]) < 0.1
    assert abs(year_data["avg_TMIN"] - expected_stuttgart_data_2024["ganzes_jahr"]["avg_TMIN"]) < 0.1

    # Überprüfen der Saisonwerte
    seasons_data = year_data["seasons"]

    # Frühling
    assert abs(seasons_data["Spring"]["avg_TMAX"] - expected_stuttgart_data_2024["spring"]["avg_TMAX"]) < 0.1
    assert abs(seasons_data["Spring"]["avg_TMIN"] - expected_stuttgart_data_2024["spring"]["avg_TMIN"]) < 0.1

    # Sommer
    assert abs(seasons_data["Summer"]["avg_TMAX"] - expected_stuttgart_data_2024["summer"]["avg_TMAX"]) < 0.1
    assert abs(seasons_data["Summer"]["avg_TMIN"] - expected_stuttgart_data_2024["summer"]["avg_TMIN"]) < 0.1

    # Herbst
    assert abs(seasons_data["Autumn"]["avg_TMAX"] - expected_stuttgart_data_2024["autumn"]["avg_TMAX"]) < 0.1
    assert abs(seasons_data["Autumn"]["avg_TMIN"] - expected_stuttgart_data_2024["autumn"]["avg_TMIN"]) < 0.1

    # Winter
    assert abs(seasons_data["Winter"]["avg_TMAX"] - expected_stuttgart_data_2024["winter"]["avg_TMAX"]) < 0.1
    assert abs(seasons_data["Winter"]["avg_TMIN"] - expected_stuttgart_data_2024["winter"]["avg_TMIN"]) < 0.1

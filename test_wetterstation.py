import pytest
import json
from flask import Flask
from server import app, parse_stations, process_weather_data_for_station, search_stations


# ----------- FIXTURES -----------
@pytest.fixture
def client():
    """Test-Client für die Flask-Anwendung."""
    app.testing = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_stations():
    """Stellt Mock-Daten für Stationen bereit."""
    return [
        {"id": "USW00094728", "name": "BOSTON LOGAN INTERNATIONAL AIRPORT", "lat": 42.3601, "lon": -71.0589},
        {"id": "USW00023234", "name": "NEW YORK CENTRAL PARK", "lat": 40.7128, "lon": -74.0060},
    ]


# ----------- ROUTEN TESTEN -----------
def test_search_stations_valid(client, mock_stations, monkeypatch):
    """Testet den Endpunkt '/search_stations' mit gültigen Parametern."""
    # Mock für die Stationsdaten (Patchen der Funktion)
    monkeypatch.setattr('server.stations', mock_stations)

    response = client.get("/search_stations?lat=42.36&lon=-71.05")
    data = response.get_json()

    assert response.status_code == 200
    assert len(data) > 0
    assert "id" in data[0] and "name" in data[0]


def test_search_stations_invalid_parameters(client):
    """Testet den Endpunkt '/search_stations' mit ungültigen Parametern."""
    response = client.get("/search_stations?lat=invalid&lon=invalid")
    data = response.get_json()

    assert response.status_code == 400
    assert "error" in data
    assert data["error"] == "Ungültige Parameter"


def test_get_station_data_valid(client, mock_stations, monkeypatch):
    """Test für den Endpunkt '/get_station_data' mit einer gültigen Station-ID."""
    # Mock für Stationsdaten
    monkeypatch.setattr('server.stations', mock_stations)

    station_id = "USW00094728"
    response = client.get(f"/get_station_data?station_id={station_id}&start_year=2020&end_year=2022")
    data = response.get_json()

    assert response.status_code == 200
    assert "id" in data and data["id"] == station_id


def test_get_station_data_not_found(client):
    """Test für den Endpunkt '/get_station_data' mit einer ungültigen Station-ID."""
    response = client.get("/get_station_data?station_id=invalid_id")
    data = response.get_json()

    assert response.status_code == 404
    assert "error" in data
    assert data["error"] == "Station nicht gefunden"


# ----------- FUNKTIONS-TESTS -----------
def test_parse_stations(monkeypatch, tmpdir):
    """Testet die Funktion parse_stations mit einer temporären Datei."""
    # Temporäre Datei mit Testdaten
    stations_file = tmpdir.join("stations.txt")
    stations_file.write("USW00094728  42.3601 -71.0589 123.4 BOSTON LOGAN INTERNATIONAL AIRPORT     MA US\n"
                        "USW00023234  40.7128 -74.0060 123.4 NEW YORK CENTRAL PARK                 NY US\n")

    monkeypatch.setattr('server.STATIONS_FILE', str(stations_file))
    stations = parse_stations()

    assert len(stations) == 2
    assert stations[0]["name"] == "BOSTON LOGAN INTERNATIONAL AIRPORT"
    assert stations[1]["name"] == "NEW YORK CENTRAL PARK"


def test_process_weather_data_for_station(monkeypatch, tmpdir):
    """Testet die Funktion process_weather_data_for_station mit Mock-Daten."""
    # Temporäre Wetterdatei vorbereiten
    weather_file = tmpdir.join("USW00094728.dly")
    weather_file.write(
        "20220101TMAX 1234\n"
        "20220101TMIN -567\n"
    )

    monkeypatch.setattr('server.WEATHER_DATA_DIR', str(tmpdir))
    temps, error = process_weather_data_for_station("USW00094728")

    assert temps is not None
    assert len(temps) > 0
    assert error is None


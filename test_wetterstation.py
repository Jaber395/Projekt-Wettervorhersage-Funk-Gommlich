import pytest
from server import app  # Importieren Sie Ihre Flask-App

"Start mit server"
@pytest.fixture
def client():
    """Test-Client für die Flask-Anwendung."""
    with app.test_client() as client:
        yield client


def test_search_stations_valid(client):
    """Test für den Endpunkt '/search_stations' mit gültigen Parametern."""
    response = client.get("/search_stations?lat=50.0&lon=8.0&radius=100&max=5")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    # Überprüfen, ob das Ergebnis korrekt formatiert ist
    for station in data:
        assert "id" in station
        assert "lat" in station
        assert "lon" in station
        assert "name" in station
        assert "distance" in station


def test_search_stations_invalid_parameters(client):
    """Test für den Endpunkt '/search_stations' mit ungültigen Parametern."""
    response = client.get("/search_stations?lat=invalid&lon=invalid")
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Ungültige Parameter"


def test_get_station_data_valid(client):
    """Test für den Endpunkt '/get_station_data' mit einer gültigen Station-ID."""
    # Eine vorhandene Station-ID aus Ihrer Liste von Stationen testen
    station_id = "12345678901"  # Beispiel-ID (ändern Sie dies bei Bedarf)
    response = client.get(f"/get_station_data?station_id={station_id}&start_year=2010&end_year=2020")
    assert response.status_code == 200
    data = response.get_json()
    assert "station" in data
    assert "annual_data" in data
    assert "seasonal_data" in data

    # Überprüfen der Datenstruktur
    assert len(data["annual_data"]) > 0
    for year_data in data["annual_data"]:
        assert "year" in year_data
        assert "annual_min" in year_data
        assert "annual_max" in year_data


def test_get_station_data_not_found(client):
    """Test für den Endpunkt '/get_station_data' mit einer ungültigen Station-ID."""
    response = client.get("/get_station_data?station_id=invalid_id")
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Station nicht gefunden"


def test_get_station_data_invalid_years(client):
    """Test für den Endpunkt '/get_station_data' mit ungültigen Jahreswerten."""
    response = client.get("/get_station_data?station_id=12345678901&start_year=invalid&end_year=invalid")
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Ungültige Jahresangaben"

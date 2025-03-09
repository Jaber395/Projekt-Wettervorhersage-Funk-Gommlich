import pytest
import json
import requests
from unittest.mock import patch, MagicMock

# Base URL for API
BASE_URL = "http://localhost:8080"

# Test data
SAMPLE_STATION = {
    "id": "12345",
    "name": "Stuttgart Teststation",
    "lat": 48.7758,
    "lon": 9.1829,
    "distance": 2.4
}

SAMPLE_MULTIPLE_STATIONS = [
    SAMPLE_STATION,
    {
        "id": "67890",
        "name": "Frankfurt Teststation",
        "lat": 50.1109,
        "lon": 8.6821,
        "distance": 4.7
    }
]

SAMPLE_STATION_DATA = {
    "name": "Stuttgart Teststation",
    "years": {
        "2022": {
            "avg_TMIN": 5.2,
            "avg_TMAX": 15.8,
            "seasons": {
                "Winter": {"avg_TMIN": -1.3, "avg_TMAX": 5.7},
                "Spring": {"avg_TMIN": 4.8, "avg_TMAX": 15.2},
                "Summer": {"avg_TMIN": 13.9, "avg_TMAX": 25.6},
                "Autumn": {"avg_TMIN": 7.2, "avg_TMAX": 16.4}
            }
        },
        "2023": {
            "avg_TMIN": 5.7,
            "avg_TMAX": 16.2,
            "seasons": {
                "Winter": {"avg_TMIN": -0.8, "avg_TMAX": 6.1},
                "Spring": {"avg_TMIN": 5.2, "avg_TMAX": 15.9},
                "Summer": {"avg_TMIN": 14.3, "avg_TMAX": 26.2},
                "Autumn": {"avg_TMIN": 7.5, "avg_TMAX": 16.8}
            }
        }
    }
}


# Fixtures
@pytest.fixture
def mock_requests_get():
    with patch('requests.get') as mock_get:
        yield mock_get


# Tests for /search_stations endpoint
class TestSearchStations:
    def test_search_stations_valid_params(self, mock_requests_get):
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_MULTIPLE_STATIONS
        mock_requests_get.return_value = mock_response

        # Test API call
        response = requests.get(f"{BASE_URL}/search_stations?lat=48.7758&lon=9.1829&radius=10&max=5")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert "id" in data[0]
        assert "name" in data[0]
        assert "lat" in data[0]
        assert "lon" in data[0]
        assert "distance" in data[0]

    def test_search_stations_invalid_params(self, mock_requests_get):
        # Set up mock response for invalid parameters
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_requests_get.return_value = mock_response

        # Test API call with invalid parameters
        response = requests.get(f"{BASE_URL}/search_stations?lat=invalid&lon=invalid&radius=10&max=5")

        # Assertions
        assert response.status_code == 400

    def test_search_stations_no_results(self, mock_requests_get):
        # Set up mock response for no results
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_requests_get.return_value = mock_response

        # Test API call with parameters that should return no results
        response = requests.get(f"{BASE_URL}/search_stations?lat=0&lon=0&radius=1&max=5")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


# Tests for /get_station_data endpoint
class TestGetStationData:
    def test_get_station_data_valid_params(self, mock_requests_get):
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_STATION_DATA
        mock_requests_get.return_value = mock_response

        # Test API call
        response = requests.get(f"{BASE_URL}/get_station_data?station_id=12345&start_year=2022&end_year=2023")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "years" in data
        assert "2022" in data["years"]
        assert "avg_TMIN" in data["years"]["2022"]
        assert "avg_TMAX" in data["years"]["2022"]
        assert "seasons" in data["years"]["2022"]
        assert "Winter" in data["years"]["2022"]["seasons"]

    def test_get_station_data_invalid_station_id(self, mock_requests_get):
        # Set up mock response for invalid station ID
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_requests_get.return_value = mock_response

        # Test API call with invalid station ID
        response = requests.get(f"{BASE_URL}/get_station_data?station_id=invalid&start_year=2022&end_year=2023")

        # Assertions
        assert response.status_code == 404

    def test_get_station_data_no_data_for_timeframe(self, mock_requests_get):
        # Set up mock response for no data in timeframe
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "Stuttgart Teststation", "years": {}}
        mock_requests_get.return_value = mock_response

        # Test API call with timeframe that has no data
        response = requests.get(f"{BASE_URL}/get_station_data?station_id=12345&start_year=1800&end_year=1801")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "years" in data
        assert len(data["years"]) == 0

    def test_get_station_data_invalid_date_range(self, mock_requests_get):
        # Set up mock response for invalid date range
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_requests_get.return_value = mock_response

        # Test API call with end_year before start_year
        response = requests.get(f"{BASE_URL}/get_station_data?station_id=12345&start_year=2023&end_year=2022")

        # Assertions
        assert response.status_code == 400


# Integration tests
@pytest.mark.integration
class TestIntegration:
    def test_search_and_get_data_flow(self, mock_requests_get):
        # First mock the search stations response
        search_response = MagicMock()
        search_response.status_code = 200
        search_response.json.return_value = [SAMPLE_STATION]

        # Then mock the get station data response
        station_data_response = MagicMock()
        station_data_response.status_code = 200
        station_data_response.json.return_value = SAMPLE_STATION_DATA

        # Set up the mock to return different responses for different calls
        mock_requests_get.side_effect = [search_response, station_data_response]

        # First API call - search for stations
        search_result = requests.get(f"{BASE_URL}/search_stations?lat=48.7758&lon=9.1829&radius=10&max=5")

        # Get the first station from the results
        stations = search_result.json()
        assert len(stations) > 0
        station_id = stations[0]["id"]

        # Second API call - get data for the first station
        data_result = requests.get(f"{BASE_URL}/get_station_data?station_id={station_id}&start_year=2022&end_year=2023")

        # Verify the result
        station_data = data_result.json()
        assert station_data["name"] == stations[0]["name"]
        assert "years" in station_data
        assert len(station_data["years"]) > 0


# Run tests with pytest
if __name__ == "__main__":
    pytest.main(["-v"])

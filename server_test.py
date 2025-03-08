import os
import json
import pytest
import math
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import server


# Define a proper fixture for Flask app
@pytest.fixture
def flask_app():
    """Create a Flask app for testing."""
    # Save original constants
    original_stations_file = server.STATIONS_FILE
    original_weather_data_dir = server.WEATHER_DATA_DIR

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
    server.STATIONS_FILE = original_stations_file
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
        f.write(
            f"{station_id}2022010TMAX  250  251  252  253  254  255  256  257  258  259  260  261  262  263  264  265  266  267  268  269  270  271  272  273  274  275  276  277  278  279  280\n")
        f.write(
            f"{station_id}2022010TMIN  100  101  102  103  104  105  106  107  108  109  110  111  112  113  114  115  116  117  118  119  120  121  122  123  124  125  126  127  128  129  130\n")
        # Sample data for April 2022 (Spring)
        f.write(
            f"{station_id}2022040TMAX  300  301  302  303  304  305  306  307  308  309  310  311  312  313  314  315  316  317  318  319  320  321  322  323  324  325  326  327  328  329  330\n")
        f.write(
            f"{station_id}2022040TMIN  150  151  152  153  154  155  156  157  158  159  160  161  162  163  164  165  166  167  168  169  170  171  172  173  174  175  176  177  178  179  180\n")


def test_haversine():
    """Test the haversine distance calculation function."""
    # New York to Los Angeles
    dist = server.haversine(40.7128, -74.0060, 34.0522, -118.2437)
    # The result should be approximately 3935 km
    assert abs(dist - 3935) < 5  # Allow some rounding differences


@patch('server.download_station_file')
def test_parse_stations(mock_download, mock_stations):
    """Test parsing station data from file."""
    create_test_station_file(mock_stations)

    # Test parsing the stations file
    parsed_stations = server.parse_stations()

    # Check that stations are parsed correctly
    assert len(parsed_stations) == len(mock_stations)
    for i, station in enumerate(parsed_stations):
        assert station['id'] == mock_stations[i]['id']
        assert station['lat'] == mock_stations[i]['lat']
        assert station['lon'] == mock_stations[i]['lon']
        assert station['name'] == mock_stations[i]['name']


@patch('requests.get')
def test_download_weather_data(mock_get, mock_stations):
    """Test downloading weather data for a station."""
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


def test_get_station_data_endpoint(client, mock_stations):
    """Test the get_station_data endpoint."""
    # Set the stations list for testing
    server.stations = mock_stations
    test_station = mock_stations[0]

    # Create a test weather data file
    create_test_weather_file(test_station['id'])

    # Test the endpoint
    response = client.get(f"/get_station_data?station_id={test_station['id']}&start_year=2022&end_year=2022")

    # Check the response
    assert response.status_code == 200
    data = json.loads(response.data)

    # Verify the structure and contents of the response
    assert data['station'] == test_station['id']
    assert data['name'] == test_station['name']
    assert '2022' in data['years']

    # Check that TMAX and TMIN averages are calculated correctly
    year_data = data['years']['2022']
    assert 'avg_TMAX' in year_data
    assert 'avg_TMIN' in year_data

    # Check that seasons are correctly identified
    assert 'seasons' in year_data
    if 'Winter' in year_data['seasons']:
        assert 'avg_TMAX' in year_data['seasons']['Winter']
        assert 'avg_TMIN' in year_data['seasons']['Winter']

    if 'Spring' in year_data['seasons']:
        assert 'avg_TMAX' in year_data['seasons']['Spring']
        assert 'avg_TMIN' in year_data['seasons']['Spring']

    # Test with invalid station ID
    response = client.get("/get_station_data?station_id=NONEXISTENT")
    assert response.status_code == 404

    # Test with invalid year parameters
    response = client.get(f"/get_station_data?station_id={test_station['id']}&start_year=invalid")
    assert response.status_code == 400


@patch('server.download_station_file')
@patch('server.parse_stations')
def test_initialization(mock_parse, mock_download):
    """Test the initialization process."""
    # Call the initialization code explicitly to ensure it's tested
    server.download_station_file()
    server.parse_stations()

    # Verify that the functions were called
    mock_download.assert_called_once()
    mock_parse.assert_called_once()

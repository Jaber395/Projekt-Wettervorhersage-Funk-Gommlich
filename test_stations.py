import json
import os


def test_stations_json_exists():
    """Test that the stations.json file exists"""
    assert os.path.exists('stations.json')


def test_stations_json_loads():
    """Test that the stations.json file can be loaded as valid JSON"""
    with open('stations.json', 'r', encoding='utf-8') as f:
        stations = json.load(f)
    assert isinstance(stations, list)
    assert len(stations) > 0


def test_stations_structure():
    """Test that each station has the required structure"""
    with open('stations.json', 'r', encoding='utf-8') as f:
        stations = json.load(f)

    required_keys = ["name", "latitude", "longitude", "temperature"]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    for station in stations:
        # Check that each station has all required keys
        for key in required_keys:
            assert key in station, f"Station missing required key: {key}"

        # Check coordinates are within valid ranges
        assert -90 <= station["latitude"] <= 90, f"Invalid latitude for {station['name']}"
        assert -180 <= station["longitude"] <= 180, f"Invalid longitude for {station['name']}"

        # Check temperature data structure
        assert isinstance(station["temperature"], dict), "Temperature should be a dictionary"

        # Check that all months are present
        for month in months:
            assert month in station["temperature"], f"Month {month} missing for {station['name']}"

        # Verify that temperatures are numeric
        for month, temp in station["temperature"].items():
            assert isinstance(temp, (int, float)), f"Temperature for {month} is not a number"


def test_station_names_unique():
    """Test that all station names are unique"""
    with open('stations.json', 'r', encoding='utf-8') as f:
        stations = json.load(f)

    names = [station["name"] for station in stations]
    assert len(names) == len(set(names)), "Station names should be unique"


def test_temperature_ranges():
    """Test that temperature values are within reasonable ranges for Germany"""
    with open('stations.json', 'r', encoding='utf-8') as f:
        stations = json.load(f)

    for station in stations:
        for month, temp in station["temperature"].items():
            # German temperature ranges (adjust if needed)
            assert -20 <= temp <= 40, f"Temperature {temp}°C for {month} at {station['name']} outside reasonable range"

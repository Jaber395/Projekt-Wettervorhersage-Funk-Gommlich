import os
import re
import pytest
from unittest.mock import patch, MagicMock


def test_js_file_exists():
    """Test that the JavaScript file exists"""
    assert os.path.exists('script.js')


def test_js_syntax():
    """Test basic JavaScript syntax"""
    with open('script.js', 'r', encoding='utf-8') as f:
        js_content = f.read()

    # Check for matching braces/parentheses/brackets
    opening_chars = {'(': ')', '{': '}', '[': ']'}
    stack = []

    for char in js_content:
        if char in opening_chars:
            stack.append(char)
        elif char in opening_chars.values():
            if not stack or opening_chars[stack.pop()] != char:
                pytest.fail(f"Mismatched braces in JavaScript file")

    assert len(stack) == 0, "Unmatched opening braces in JavaScript file"


def test_js_has_event_listeners():
    """Test that DOMContentLoaded event listeners are defined"""
    with open('script.js', 'r', encoding='utf-8') as f:
        js_content = f.read()

    assert "document.addEventListener(\"DOMContentLoaded\"" in js_content, "Missing DOMContentLoaded event listener"
    # Count event listeners
    num_listeners = js_content.count("document.addEventListener(\"DOMContentLoaded\"")
    assert num_listeners >= 1, "Should have at least one DOMContentLoaded event listener"


def test_js_chart_initialization():
    """Test that Chart initialization is present"""
    with open('script.js', 'r', encoding='utf-8') as f:
        js_content = f.read()

    assert "new Chart(" in js_content, "Chart initialization missing"
    assert "temperatureChart" in js_content, "Temperature chart reference missing"


def test_map_functionality():
    """Test that map functionality is present"""
    with open('script.js', 'r', encoding='utf-8') as f:
        js_content = f.read()

    # Check for Leaflet map initialization
    assert "L.map(" in js_content, "Leaflet map initialization missing"
    assert "L.tileLayer(" in js_content, "Map tile layer missing"

    # Check for marker functions
    assert "addStationMarker" in js_content, "Add marker function missing"
    assert "clearMap" in js_content, "Clear map function missing"


def test_distance_calculation():
    """Test that distance calculation function is present"""
    with open('script.js', 'r', encoding='utf-8') as f:
        js_content = f.read()

    assert "getDistance" in js_content, "Distance calculation function missing"
    assert "Math.sin" in js_content, "Trigonometric functions for distance calculation missing"


def test_json_loading():
    """Test that JSON loading functionality is present"""
    with open('script.js', 'r', encoding='utf-8') as f:
        js_content = f.read()

    assert "fetch(" in js_content, "Fetch API call missing"
    assert "stations.json" in js_content, "Reference to stations.json missing"


def test_function_dependencies():
    """Test if the script references all needed HTML elements"""
    with open('script.js', 'r', encoding='utf-8') as f:
        js_content = f.read()

    required_elements = [
        "temperatureChart",
        "map",
        "latitude",
        "longitude",
        "radius",
        "number",
        "year_start",
        "year_end",
        "resultsContainer"
    ]

    for element in required_elements:
        assert f"getElementById(\"{element}\")" in js_content or f"querySelector" in js_content, f"Missing reference to HTML element: {element}"


# Optional: Mock test with jsdom (would require additional setup in a real environment)
@pytest.mark.skip(reason="Requires jsdom setup")
def test_js_execution():
    """Test JavaScript execution with mocked DOM (would require jsdom)"""
    # This is a placeholder for how you might test JS execution with proper tools
    # In a real test, you'd use something like pytest-mock-browser or similar
    pass

import pytest
from bs4 import BeautifulSoup

@pytest.fixture
def html_content():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

def test_html_structure(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Prüfen, ob die HTML-Struktur korrekt ist
    assert soup.find("title"), "Die HTML-Datei hat keinen <title>-Tag."
    assert soup.find("body"), "Die HTML-Datei hat keinen <body>-Tag."
    assert soup.find("h1"), "Es fehlt eine Hauptüberschrift <h1>."
    
    # Prüfen, ob wichtige Sektionen vorhanden sind
    assert soup.find(id="loading-overlay"), "Das Lade-Overlay fehlt."
    assert soup.find("div", class_="section-search"), "Die Such-Sektion fehlt."
    assert soup.find("div", class_="section-results"), "Die Ergebnis-Sektion fehlt."

def test_input_fields_exist(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Prüfen, ob alle Eingabefelder vorhanden sind
    input_ids = ["latitude", "longitude", "radius", "number", "year-start", "year-end"]
    for input_id in input_ids:
        assert soup.find(id=input_id), f"Eingabefeld mit ID '{input_id}' fehlt."

def test_button_exists(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Prüfen, ob der Such-Button vorhanden ist
    assert soup.find("button", class_="button"), "Der Such-Button fehlt."

def test_map_div_exists(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Prüfen, ob die Karte vorhanden ist
    assert soup.find(id="map"), "Das <div> mit der ID 'map' fehlt."

def test_table_exists(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Prüfen, ob die Ergebnistabelle existiert
    table = soup.find("table")
    assert table, "Es gibt keine Tabelle für die Stationsdetails."
    
    # Prüfen, ob die Tabelle die richtige Struktur hat
    assert table.find("thead"), "Die Tabelle hat keinen <thead>-Bereich."
    assert table.find("tbody", id="station-table-body"), "Die Tabelle hat keinen <tbody>-Bereich mit der richtigen ID."

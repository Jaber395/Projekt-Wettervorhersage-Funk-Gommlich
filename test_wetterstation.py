import pytest
from Wetterstation import haversine


def test_haversine():
    # Beispielwerte (zwei Punkte auf der Erde)
    lat1, lon1 = 50.0, 8.0  # Punkt 1: Frankfurt
    lat2, lon2 = 52.0, 13.0  # Punkt 2: Berlin
    distance = haversine(lat1, lon1, lat2, lon2)

    assert isinstance(distance, float)  # Überprüfen, ob Ergebnis ein float ist
    assert distance > 0  # Entfernungen sollten positiv sein
    assert round(distance) == 423  # Erwartete Entfernung in Kilometern (ungefähr)

import pandas as pd
import pytest
from Wetterstation import load_stations

def test_load_stations():
    # Die Funktion lädt Daten. Du kannst hier Beispielstationen simulieren
    stations = load_stations("stations.csv")  # Ersetze mit einem Testfile
    assert isinstance(stations, pd.DataFrame)  # Sollte ein DataFrame zurückgeben
    assert not stations.empty  # Der DataFrame sollte nicht leer sein (wenn Datei OK ist)


from Wetterstation import GHCNApp

def test_app_init():
    app = GHCNApp()  # Instance der Klasse erstellen
    assert hasattr(app, "stations_df")  # Überprüfen, ob Attribut existiert
    assert app.stations_df is None  # Beim Init sollte dies None sein




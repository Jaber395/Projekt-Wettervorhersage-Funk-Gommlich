import requests
from bs4 import BeautifulSoup
import os

def download_all_weather_data():
    base_url = "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/"
    response = requests.get(base_url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # Alle Links auf der Seite durchsuchen
        links = soup.find_all('a', href=True)
        
        # Ordner erstellen, um die Daten zu speichern
        if not os.path.exists('weather_data'):
            os.makedirs('weather_data')
        
        for link in links:
            file_name = link['href']
            if file_name.endswith('.gz'):  # Nur .gz-Dateien herunterladen
                file_url = base_url + file_name
                print(f"Lade Datei herunter: {file_name}")
                
                file_response = requests.get(file_url)
                if file_response.status_code == 200:
                    with open(f'weather_data/{file_name}', 'wb') as file:
                        file.write(file_response.content)
                    print(f"Datei {file_name} erfolgreich heruntergeladen.")
                else:
                    print(f"Fehler beim Herunterladen der Datei {file_name}: {file_response.status_code}")
    else:
        print("Fehler beim Abrufen der Website:", response.status_code)

if __name__ == "__main__":
    download_all_weather_data()
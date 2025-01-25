import requests

def download_weather_data():
    url = "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"
    response = requests.get(url)
    if response.status_code == 200:
        with open("weather_data.txt", "wb") as file:
            file.write(response.content)
        print("Wetterdaten erfolgreich heruntergeladen.")
    else:
        print("Fehler beim Herunterladen der Daten:", response.status_code)

if __name__ == "__main__":
    download_weather_data()
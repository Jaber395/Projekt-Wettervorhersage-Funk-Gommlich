// Erstellen von Diagramm mit Beispieldaten
document.addEventListener("DOMContentLoaded", function () {
    const ctx = document.getElementById('temperatureChart').getContext('2d');

    const temperatureChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({ length: 20 }, (_, i) => 2021 + i),
            datasets: [
                {
                    label: 'Min. Temperatur (°C)',
                    data: [-2, -3, -1, -2, -4, -3, -5, -4, -2, -3, -1, -2, -4, -3, -5, -4, -2, -3, -1, -2, -3],
                    borderColor: 'blue',
                    fill: false,
                },
                {
                    label: 'Max. Temperatur (°C)',
                    data: [20, 21, 22, 21, 23, 24, 25, 26, 24, 23, 22, 24, 25, 26, 27, 28, 27, 26, 25, 24, 23],
                    borderColor: 'red',
                    fill: false,
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                x: { title: { display: true, text: 'Jahr' } },
                y: { title: { display: true, text: 'Temperatur (°C)' } }
            }
        }
    });
});

// Auswahl von Start und Endjahr als Dropdownmenü
document.addEventListener("DOMContentLoaded", function () {
    const startYearSelect = document.getElementById("year_start");
    const endYearSelect = document.getElementById("year_end");

    const currentYear = new Date().getFullYear();

    for (let year = 1900; year <= 2100; year++) {
        let optionStart = new Option(year, year);
        let optionEnd = new Option(year, year);
        startYearSelect.appendChild(optionStart);
        endYearSelect.appendChild(optionEnd);
    }

    startYearSelect.value = currentYear - 1;
    endYearSelect.value = currentYear;
});

document.addEventListener("DOMContentLoaded", async function () {
    // Initialisiere die Karte mit Standard-Koordinaten
    const map = L.map('map').setView([48.7758, 9.1829], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    let currentMarkers = [];
    let currentCircle = null;

    // Beispielstationen aus der JSON-Datei laden
    let stations = [];
    try {
        const response = await fetch("stations.json");
        stations = await response.json();
    } catch (error) {
        console.error("Fehler beim Laden der Stationsdaten:", error);
    }

    function addStationMarker(lat, lng, name) {
        const marker = L.marker([lat, lng], {
            icon: L.icon({ 
                iconUrl: 'https://www.google.com/mapfiles/ms/icons/blue-dot.png',
                iconSize: [32, 32]
            })
        }).addTo(map)
          .bindPopup(`<b>${name}</b><br>(${lat}, ${lng})`);

        currentMarkers.push(marker);
    }

    function clearMap() {
        currentMarkers.forEach(marker => map.removeLayer(marker));
        currentMarkers = [];
        if (currentCircle) {
            map.removeLayer(currentCircle);
            currentCircle = null;
        }

        // Trefferliste leeren
        document.getElementById("resultsContainer").innerHTML = "";
    }

    function getDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // Erdradius in km
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c; // Entfernung in km
    }

    document.querySelector(".button").addEventListener("click", function () {
        const lat = parseFloat(document.getElementById("latitude").value);
        const lng = parseFloat(document.getElementById("longitude").value);
        const radius = parseFloat(document.getElementById("radius").value);
        const maxStations = parseInt(document.getElementById("number").value);

        if (!isNaN(lat) && !isNaN(lng) && !isNaN(radius)) {
            clearMap();

            // Kreis um die Suchkoordinaten hinzufügen
            currentCircle = L.circle([lat, lng], {
                color: '#add8e6',
                fillColor: '#add8e6',
                fillOpacity: 0.3,
                radius: radius * 1000
            }).addTo(map);

            // Stationen mit Entfernungsberechnung sammeln
            let nearbyStations = stations.map(station => {
                return {
                    ...station,
                    distance: getDistance(lat, lng, station.latitude, station.longitude)
                };
            });

            // Nur Stationen innerhalb des Radius behalten & nach Entfernung sortieren
            nearbyStations = nearbyStations
                .filter(station => station.distance <= radius)
                .sort((a, b) => a.distance - b.distance) // Nach Nähe sortieren
                .slice(0, maxStations); // Begrenzung auf max. Anzahl

            // Trefferliste-Container
            const resultsContainer = document.getElementById("resultsContainer");

            // Stationen auf die Karte setzen & Buttons erstellen
            nearbyStations.forEach(station => {
                addStationMarker(station.latitude, station.longitude, station.name);

                // Treffer als Button hinzufügen
                const stationButton = document.createElement("button");
                stationButton.classList.add("station-button");
                stationButton.innerHTML = `${station.name} - ${station.distance.toFixed(2)} km`;
                stationButton.addEventListener("click", function () {
                    map.setView([station.latitude, station.longitude], 12);
                });

                resultsContainer.appendChild(stationButton);
            });

            map.setView([lat, lng], 10);
        } else {
            alert("Bitte gültige Koordinaten, einen Radius und eine Anzahl eingeben!");
        }
    });
});


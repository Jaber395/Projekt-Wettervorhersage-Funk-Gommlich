document.addEventListener("DOMContentLoaded", function () {
    // Karte initialisieren
    const map = L.map('map').setView([48.064869, 8.535076], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    let currentMarkers = [];
    let currentCircle = null;
    let centerMarker = null;

    // Markierungen auf der Karte hinzufügen
    function addStationMarker(lat, lng, name, stationId) {
        const marker = L.marker([lat, lng], {
            icon: L.icon({ 
                iconUrl: 'https://www.google.com/mapfiles/ms/icons/blue-dot.png',
                iconSize: [32, 32]
            })
        }).addTo(map)
          .bindPopup(`<b>${name}: ${stationId}</b><br>(${lat}, ${lng})`);

        currentMarkers.push(marker);
    }

    // Karte leeren
    function clearMap() {
        currentMarkers.forEach(marker => map.removeLayer(marker));
        currentMarkers = [];
        
        if (currentCircle) {
            map.removeLayer(currentCircle);
            currentCircle = null;
        }
    
        if (centerMarker) {
            map.removeLayer(centerMarker);
            centerMarker = null;
        }
    
        document.getElementById("results-container").innerHTML = "";
    
        document.getElementById("station-title").innerText = "Stationsdetails";
    
        document.getElementById("station-table-body").innerHTML = "<tr><td colspan='11'>Keine Daten verfügbar</td></tr>";
    
        temperatureChart.data.labels = [];
        temperatureChart.data.datasets.forEach(dataset => dataset.data = []);
        temperatureChart.update();
    }
    
    document.querySelector(".button").addEventListener("click", function () {
        const lat = parseFloat(document.getElementById("latitude").value);
        const lon = parseFloat(document.getElementById("longitude").value);
        const radius = parseFloat(document.getElementById("radius").value);
        const maxStations = parseInt(document.getElementById("number").value);
        
        const startYear = parseInt(document.getElementById("year-start").value);
        const endYear = parseInt(document.getElementById("year-end").value);
    
        if (!isNaN(lat) && !isNaN(lon) && !isNaN(radius)) {
            clearMap();
            showLoading();
    
            currentCircle = L.circle([lat, lon], {
                color: '#004d99',
                fillColor: '#add8e6',
                fillOpacity: 0.3,
                radius: radius * 1000
            }).addTo(map);
    
            centerMarker = L.marker([lat, lon], {
                icon: L.icon({
                    iconUrl: 'https://www.google.com/mapfiles/ms/icons/red-dot.png',
                    iconSize: [32, 32]
                })
            }).addTo(map).bindPopup(`<b>Mittelpunkt</b><br>(${lat.toFixed(5)}, ${lon.toFixed(5)})`);
    
            // ➡️ Hier haben wir start_year und end_year ergänzt!
            fetch(`http://localhost:8080/search_stations?lat=${lat}&lon=${lon}&radius=${radius}&max=${maxStations}&start_year=${startYear}&end_year=${endYear}`)
                .then(response => response.json())
                .then(data => {
                    hideLoading();
    
                    const resultsContainer = document.getElementById("results-container");
                    resultsContainer.innerHTML = "";
    
                    data.forEach(station => {
                        addStationMarker(station.lat, station.lon, station.name, station.id);
    
                        const stationButton = document.createElement("button");
                        stationButton.classList.add("station-button");
                        stationButton.innerHTML = `${station.name} - ${station.distance.toFixed(1)} km`;
    
                        stationButton.addEventListener("click", function () {
                            fetchStationData(station.id);
                            map.setView([station.lat, station.lon], 12);
                        });
    
                        resultsContainer.appendChild(stationButton);
                    });
    
                    map.setView([lat, lon], 10);
                })
                .catch(error => {
                    hideLoading();
                    console.error("Fehler beim Abrufen der Daten:", error);
                });
        } else {
            alert("Bitte gültige Koordinaten, einen Radius und eine Anzahl eingeben!");
        }
    });
    
   
    // Lade Overlay anzeigen
    function showLoading() {
        document.getElementById("loading-overlay").style.display = "flex";
    }
    
    // Lade Overlay ausblenden
    function hideLoading() {
        document.getElementById("loading-overlay").style.display = "none";
    }
    
    //  Chart initiieren
    const ctx = document.getElementById('temp-chart').getContext('2d');
    const temperatureChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: '∅-Jahresminima', data: [], borderColor: 'blue', fill: false, spanGaps: false },
                { label: '∅-Jahresmaxima', data: [], borderColor: 'red', fill: false, spanGaps: false },
                { label: '∅-Frühling Minima', data: [], borderColor: '#0d8b22', fill: false, hidden: true, spanGaps: false },
                { label: '∅-Frühling Maxima', data: [], borderColor: '#0bfd68', fill: false, hidden: true, spanGaps: false },
                { label: '∅-Sommer Minima', data: [], borderColor: '#dac82d', fill: false, hidden: true, spanGaps: false },
                { label: '∅-Sommer Maxima', data: [], borderColor: '#fdee64', fill: false, hidden: true, spanGaps: false },
                { label: '∅-Herbst Minima', data: [], borderColor: '#925115', fill: false, hidden: true, spanGaps: false },
                { label: '∅-Herbst Maxima', data: [], borderColor: '#ff8c49', fill: false, hidden: true, spanGaps: false },
                { label: '∅-Winter Minima', data: [], borderColor: '#2b8392', fill: false, hidden: true, spanGaps: false },
                { label: '∅-Winter Maxima', data: [], borderColor: '#49e4ff', fill: false, hidden: true, spanGaps: false }
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

    // Stationsdaten holen und verarbeiten
    function fetchStationData(stationId) {
        const startYear = parseInt(document.getElementById("year-start").value);
        const endYear = parseInt(document.getElementById("year-end").value);
    
        fetch(`http://localhost:8080/get_station_data?station_id=${stationId}&start_year=${startYear}&end_year=${endYear}`)
            .then(response => response.json())
            .then(data => {
                if (!data || !data.years || Object.keys(data.years).length === 0) {
                    console.error("Fehler: API-Antwort hat keine gültigen Jahresdaten!", data);
                    alert("Fehler: Keine gültigen Jahresdaten verfügbar.");
                    return;
                }
    
                document.getElementById("station-title").innerText = `Stationsdetails: ${data.name}`;
    
                // Vollständige Liste an Jahren erzeugen
                const labels = [];
                for (let year = startYear; year <= endYear; year++) {
                    labels.push(year.toString());
                }
    
                // Hilfsfunktion um die Daten zu füllen, fehlende Werte als null
                function fillData(prop) {
                    return labels.map(year => {
                        const yearData = data.years[year];
                        return yearData ? (yearData[prop] ?? null) : null;
                    });
                }
    
                // Hilfsfunktion für Seasons-Daten
                function fillSeasonData(season, prop) {
                    return labels.map(year => {
                        const yearData = data.years[year];
                        return yearData && yearData.seasons && yearData.seasons[season]
                            ? (yearData.seasons[season][prop] ?? null)
                            : null;
                    });
                }
    
                temperatureChart.data.labels = labels;
                temperatureChart.data.datasets[0].data = fillData("avg_TMIN");
                temperatureChart.data.datasets[1].data = fillData("avg_TMAX");

                const seasons = ["Spring", "Summer", "Autumn", "Winter"];
                const lat = parseFloat(document.getElementById("latitude").value);

                const originalSeasons = ["Spring", "Summer", "Autumn", "Winter"];
                const adjustedSeasons = lat < 0 ? ["Autumn", "Winter", "Spring", "Summer"] : originalSeasons;

                let datasetIndex = 2;
                for (let i = 0; i < originalSeasons.length; i++) {
                    let season = originalSeasons[i];
                    let adjustedSeason = adjustedSeasons[i];

                    temperatureChart.data.datasets[datasetIndex].data = fillSeasonData(adjustedSeason, "avg_TMIN");
                    datasetIndex++;
                    temperatureChart.data.datasets[datasetIndex].data = fillSeasonData(adjustedSeason, "avg_TMAX");
                    datasetIndex++;
                }


                temperatureChart.update();
                updateTable(data)

            })
            .catch(error => {
                console.error("Fehler beim Abrufen der Stationsdaten:", error);
                alert("Fehler beim Abrufen der Stationsdaten. Siehe Konsole für Details.");
            });
    }
    
    
    // Tabelle aktualisieren
    function updateTable(data) {
        let tableBody = document.getElementById("station-table-body");
        tableBody.innerHTML = "";
    
        if (!data.years || Object.keys(data.years).length === 0) {
            tableBody.innerHTML = "<tr><td colspan='11'>Keine Daten verfügbar</td></tr>";
            return;
        }
    
        const lat = parseFloat(document.getElementById("latitude").value);
        
        function adjustSeasonForSouthernHemisphere(season) {
            if (lat < 0) {
                const seasonMapping = {
                    "Spring":"Autumn",
                    "Summer":"Winter",
                    "Autumn":"Spring",
                    "Winter":"Summer",
                };
                return seasonMapping[season] || season;
            }
            return season;
        }
    
        Object.keys(data.years).forEach(year => {
            let yearData = data.years[year];
            let row = `<tr>
                <td>${year}</td>
                <td>${yearData.avg_TMIN !== null ? yearData.avg_TMIN + "°C" : "-"}</td>
                <td>${yearData.avg_TMAX !== null ? yearData.avg_TMAX + "°C" : "-"}</td>`;
    
            const seasons = [ "Spring", "Summer", "Autumn", "Winter"];
            
            seasons.forEach(season => {
                let adjustedSeason = adjustSeasonForSouthernHemisphere(season);
                let seasonData = yearData.seasons[adjustedSeason] || {};
                
                let minTemp = seasonData.avg_TMIN == null ? "-" : seasonData.avg_TMIN + "°C";
                let maxTemp = seasonData.avg_TMAX == null ? "-" : seasonData.avg_TMAX + "°C";
                
                row += `<td>${minTemp}</td><td>${maxTemp}</td>`;
            });
    
            row += "</tr>";
            tableBody.innerHTML += row;
        });
    }
    
    // Dropdown-Menü für Jahreseingabe erstellen
    const startYearSelect = document.getElementById("year-start");
    const endYearSelect = document.getElementById("year-end");
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

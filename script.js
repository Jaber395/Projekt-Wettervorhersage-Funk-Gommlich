document.addEventListener("DOMContentLoaded", function () {
    // 🌍 Karte initialisieren
    const map = L.map('map').setView([48.7758, 9.1829], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    let currentMarkers = [];
    let currentCircle = null;
    let centerMarker = null;

    function addStationMarker(lat, lng, name, stationId) {
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
    
        if (centerMarker) {
            map.removeLayer(centerMarker);
            centerMarker = null;
        }
    
        document.getElementById("resultsContainer").innerHTML = "";
    
        document.getElementById("stationTitle").innerText = "Stationsdetails";
    
        document.getElementById("stationDataTableBody").innerHTML = "<tr><td colspan='11'>Keine Daten verfügbar</td></tr>";
    
        temperatureChart.data.labels = [];
        temperatureChart.data.datasets.forEach(dataset => dataset.data = []);
        temperatureChart.update();
    }
    
    document.querySelector(".button").addEventListener("click", function () {
        const lat = parseFloat(document.getElementById("latitude").value);
        const lon = parseFloat(document.getElementById("longitude").value);
        const radius = parseFloat(document.getElementById("radius").value);
        const maxStations = parseInt(document.getElementById("number").value);
    
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
    
            // ⬇️ Port 8080 statt 5000
            fetch(`http://localhost:8080/search_stations?lat=${lat}&lon=${lon}&radius=${radius}&max=${maxStations}`)
                .then(response => response.json())
                .then(data => {
                    hideLoading();
    
                    const resultsContainer = document.getElementById("resultsContainer");
                    data.forEach(station => {
                        addStationMarker(station.lat, station.lon, station.name, station.id);
                        const stationButton = document.createElement("button");
                        stationButton.classList.add("station-button");
                        stationButton.innerHTML = `${station.name} - ${station.distance.toFixed(2)} km`;
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
   
    function showLoading() {
        document.getElementById("loadingOverlay").style.display = "flex";
    }
    
    function hideLoading() {
        document.getElementById("loadingOverlay").style.display = "none";
    }

    const ctx = document.getElementById('temperatureChart').getContext('2d');
    const temperatureChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: '∅-Jahresminima', data: [], borderColor: 'blue', fill: false },
                { label: '∅-Jahresmaxima', data: [], borderColor: 'red', fill: false },
                { label: '∅-Winter Minima', data: [], borderColor: '#49e4ff', fill: false, hidden: true },
                { label: '∅-Winter Maxima', data: [], borderColor: '#2b8392', fill: false, hidden: true },
                { label: '∅-Frühling Minima', data: [], borderColor: '#0bfd68', fill: false, hidden: true },
                { label: '∅-Frühling Maxima', data: [], borderColor: '#0d8b22', fill: false, hidden: true },
                { label: '∅-Sommer Minima', data: [], borderColor: '#fdee64', fill: false, hidden: true },
                { label: '∅-Sommer Maxima', data: [], borderColor: '#dac82d', fill: false, hidden: true },
                { label: '∅-Herbst Minima', data: [], borderColor: '#ff8c49', fill: false, hidden: true },
                { label: '∅-Herbst Maxima', data: [], borderColor: '#925115', fill: false, hidden: true }
            ]
        },
        options: {
            responsive: true,
            scales: {
                x: { title: { display: true, text: 'Jahr' } },
                y: { title: { display: true, text: 'Temperatur (°C)' } }
            },
            plugins: {
                legend: {
                    labels: {
                        generateLabels: function(chart) {
                            let labels = Chart.defaults.plugins.legend.labels.generateLabels(chart);
        
                            // Die ersten zwei Einträge separat setzen, der Rest kommt in eine neue Zeile
                            labels.forEach((label, index) => {
                                if (index >= 2) {
                                    label.text = '\n' + label.text; // Fügt einen Zeilenumbruch hinzu
                                }
                            });
        
                            return labels;
                        }
                    }
                }
            }
        }
    });

    function fetchStationData(stationId) {
        const startYear = document.getElementById("year_start").value;
        const endYear = document.getElementById("year_end").value;
    
        // ⬇️ Port 8080 statt 5000
        fetch(`http://localhost:8080/get_station_data?station_id=${stationId}&start_year=${startYear}&end_year=${endYear}`)
            .then(response => response.json())
            .then(data => {
                if (!data || !data.years || Object.keys(data.years).length === 0) {
                    console.error("Fehler: API-Antwort hat keine gültigen Jahresdaten!", data);
                    alert("Fehler: Keine gültigen Jahresdaten verfügbar.");
                    return;
                }
                
                document.getElementById("stationTitle").innerText = `Stationsdetails: ${data.name}`;
    
                const labels = Object.keys(data.years);
                const yearsArray = Object.entries(data.years).map(([year, values]) => ({
                    year,
                    avg_TMAX: values.avg_TMAX ?? null,
                    avg_TMIN: values.avg_TMIN ?? null,
                    seasons: values.seasons
                }));
    
                const avgTmin = yearsArray.map(entry => entry.avg_TMIN);
                const avgTmax = yearsArray.map(entry => entry.avg_TMAX);
    
                const winterTmin = yearsArray.map(entry => entry.seasons?.Winter?.avg_TMIN ?? null);
                const winterTmax = yearsArray.map(entry => entry.seasons?.Winter?.avg_TMAX ?? null);
                const springTmin = yearsArray.map(entry => entry.seasons?.Spring?.avg_TMIN ?? null);
                const springTmax = yearsArray.map(entry => entry.seasons?.Spring?.avg_TMAX ?? null);
                const summerTmin = yearsArray.map(entry => entry.seasons?.Summer?.avg_TMIN ?? null);
                const summerTmax = yearsArray.map(entry => entry.seasons?.Summer?.avg_TMAX ?? null);
                const autumnTmin = yearsArray.map(entry => entry.seasons?.Autumn?.avg_TMIN ?? null);
                const autumnTmax = yearsArray.map(entry => entry.seasons?.Autumn?.avg_TMAX ?? null);
    
                temperatureChart.data.labels = labels;
                temperatureChart.data.datasets[0].data = avgTmin;
                temperatureChart.data.datasets[1].data = avgTmax;
                temperatureChart.data.datasets[2].data = winterTmin;
                temperatureChart.data.datasets[3].data = winterTmax;
                temperatureChart.data.datasets[4].data = springTmin;
                temperatureChart.data.datasets[5].data = springTmax;
                temperatureChart.data.datasets[6].data = summerTmin;
                temperatureChart.data.datasets[7].data = summerTmax;
                temperatureChart.data.datasets[8].data = autumnTmin;
                temperatureChart.data.datasets[9].data = autumnTmax;
                temperatureChart.update();
                updateTable(data);
            })
            .catch(error => {
                console.error("Fehler beim Abrufen der Stationsdaten:", error);
                alert("Fehler beim Abrufen der Stationsdaten. Siehe Konsole für Details.");
            });
    }
    
    function updateTable(data) {
        let tableBody = document.getElementById("stationDataTableBody");
        tableBody.innerHTML = "";
    
        if (!data.years || Object.keys(data.years).length === 0) {
            tableBody.innerHTML = "<tr><td colspan='11'>Keine Daten verfügbar</td></tr>";
            return;
        }
    
        Object.keys(data.years).forEach(year => {
            let yearData = data.years[year];
            let row = `<tr>
                <td>${year}</td>
                <td>${yearData.avg_TMIN !== null ? yearData.avg_TMIN + "°C" : "-"}</td>
                <td>${yearData.avg_TMAX !== null ? yearData.avg_TMAX + "°C" : "-"}</td>`;
    
            ["Spring", "Summer", "Autumn", "Winter"].forEach(season => {
                let seasonData = yearData.seasons[season] || {};
                let minTemp = seasonData.avg_TMIN !== undefined ? seasonData.avg_TMIN + "°C" : "-";
                let maxTemp = seasonData.avg_TMAX !== undefined ? seasonData.avg_TMAX + "°C" : "-";
                row += `<td>${minTemp}</td><td>${maxTemp}</td>`;
            });
    
            row += "</tr>";
            tableBody.innerHTML += row;
        });
    }
    
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

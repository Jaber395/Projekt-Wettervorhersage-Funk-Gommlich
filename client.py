import tkinter as tk
from tkinter import ttk, messagebox
import requests
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

SERVER_URL = "http://localhost:5000"

class WeatherClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather Station Client")

        # Rahmen für die Stationssuche
        search_frame = ttk.LabelFrame(root, text="Station Suche")
        search_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ttk.Label(search_frame, text="Breite:").grid(row=0, column=0, sticky="w")
        self.lat_entry = ttk.Entry(search_frame, width=10)
        self.lat_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(search_frame, text="Länge:").grid(row=0, column=2, sticky="w")
        self.lon_entry = ttk.Entry(search_frame, width=10)
        self.lon_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(search_frame, text="Radius (km):").grid(row=1, column=0, sticky="w")
        self.radius_entry = ttk.Entry(search_frame, width=10)
        self.radius_entry.insert(0, "50")
        self.radius_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(search_frame, text="Max Ergebnisse:").grid(row=1, column=2, sticky="w")
        self.max_entry = ttk.Entry(search_frame, width=10)
        self.max_entry.insert(0, "10")
        self.max_entry.grid(row=1, column=3, padx=5, pady=5)

        self.search_button = ttk.Button(search_frame, text="Stationen suchen", command=self.search_stations)
        self.search_button.grid(row=2, column=0, columnspan=4, pady=5)

        # Listbox zur Anzeige der gefundenen Stationen
        list_frame = ttk.LabelFrame(root, text="Gefundene Stationen")
        list_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.station_listbox = tk.Listbox(list_frame, width=80, height=10)
        self.station_listbox.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.station_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.station_listbox.config(yscrollcommand=scrollbar.set)

        # Rahmen für Parameter zum Abruf der Stationsdaten
        data_frame = ttk.LabelFrame(root, text="Stationsdaten abrufen")
        data_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        ttk.Label(data_frame, text="Startjahr:").grid(row=0, column=0, sticky="w")
        self.start_year_entry = ttk.Entry(data_frame, width=10)
        self.start_year_entry.insert(0, "2010")
        self.start_year_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(data_frame, text="Endjahr:").grid(row=0, column=2, sticky="w")
        self.end_year_entry = ttk.Entry(data_frame, width=10)
        self.end_year_entry.insert(0, "2020")
        self.end_year_entry.grid(row=0, column=3, padx=5, pady=5)

        self.get_data_button = ttk.Button(data_frame, text="Daten abrufen", command=self.get_station_data)
        self.get_data_button.grid(row=1, column=0, columnspan=4, pady=5)

        # Rahmen zur textuellen Anzeige der Stationsdaten
        result_frame = ttk.LabelFrame(root, text="Stationsdaten (Text)")
        result_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.result_text = tk.Text(result_frame, height=10, wrap="none")
        self.result_text.pack(fill="both", expand=True)

        # Rahmen für die grafische Darstellung der Daten
        plot_frame = ttk.LabelFrame(root, text="Stationsdaten (Graphisch)")
        plot_frame.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")
        self.figure = plt.Figure(figsize=(6,4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Grid-Konfiguration für flexibles Layout
        root.grid_rowconfigure(1, weight=1)
        root.grid_rowconfigure(3, weight=1)
        root.grid_rowconfigure(4, weight=1)
        root.grid_columnconfigure(0, weight=1)

    def search_stations(self):
        try:
            lat = float(self.lat_entry.get())
            lon = float(self.lon_entry.get())
            radius = float(self.radius_entry.get())
            max_results = int(self.max_entry.get())
        except ValueError:
            messagebox.showerror("Fehler", "Bitte gültige numerische Werte eingeben.")
            return

        params = {"lat": lat, "lon": lon, "radius": radius, "max": max_results}
        try:
            response = requests.get(f"{SERVER_URL}/search_stations", params=params)
            response.raise_for_status()
            stations = response.json()
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Abrufen der Daten: {e}")
            return

        self.station_listbox.delete(0, tk.END)
        self.stations_data = stations
        for station in stations:
            display_text = f"{station['id']} - {station['name']} (Distanz: {station['distance']} km)"
            self.station_listbox.insert(tk.END, display_text)

    def get_station_data(self):
        selection = self.station_listbox.curselection()
        if not selection:
            messagebox.showerror("Fehler", "Bitte wählen Sie eine Station aus.")
            return
        index = selection[0]
        station = self.stations_data[index]
        station_id = station['id']

        try:
            start_year = int(self.start_year_entry.get())
            end_year = int(self.end_year_entry.get())
        except ValueError:
            messagebox.showerror("Fehler", "Bitte gültige Jahreszahlen eingeben.")
            return

        params = {"station_id": station_id, "start_year": start_year, "end_year": end_year}
        try:
            response = requests.get(f"{SERVER_URL}/get_station_data", params=params)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Abrufen der Stationsdaten: {e}")
            return

        # Textuelle Darstellung der Ergebnisse
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, "Station: " + data["station"]["name"] + "\n\n")
        self.result_text.insert(tk.END, "Jährliche Mittelwerte:\n")
        for entry in data["annual_data"]:
            self.result_text.insert(tk.END, f"Jahr {entry['year']}: Min {entry['annual_min']}°C, Max {entry['annual_max']}°C\n")
        self.result_text.insert(tk.END, "\nSaisonale Werte:\n")
        for entry in data["seasonal_data"]:
            self.result_text.insert(tk.END, f"Jahr {entry['year']}:\n")
            for season, temps in entry["seasons"].items():
                self.result_text.insert(tk.END, f"  {season}: Min {temps['min']}°C, Max {temps['max']}°C\n")

        # Grafische Darstellung: Plot der jährlichen Mittelwerte
        years = [entry["year"] for entry in data["annual_data"]]
        mins = [entry["annual_min"] for entry in data["annual_data"]]
        maxs = [entry["annual_max"] for entry in data["annual_data"]]
        self.ax.clear()
        self.ax.plot(years, mins, marker="o", label="Annual Min")
        self.ax.plot(years, maxs, marker="o", label="Annual Max")
        self.ax.set_xlabel("Jahr")
        self.ax.set_ylabel("Temperatur (°C)")
        self.ax.set_title("Jährliche Mittelwerte")
        self.ax.legend()
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherClientApp(root)
    root.mainloop()
# Verwende ein Python-Image (hier slim-Variante)
FROM python:3.10-slim

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Kopiere die requirements.txt in das Arbeitsverzeichnis
COPY requirements.txt .

# Installiere die benötigten Python-Bibliotheken
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere alle Projektdateien in das Arbeitsverzeichnis
COPY . .

# Exponiere den Container-Port, auf dem der Server läuft (server.py läuft auf 5000)
EXPOSE 8080

# Starte die Webanwendung
CMD ["python", "server.py"]

FROM python:3.10-slim

WORKDIR /app

# Kopiere die requirements.txt ins Container-Verzeichnis
COPY requirements.txt .

# Installiere Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere alle Dateien aus dem aktuellen Verzeichnis ins Container-Verzeichnis
COPY main.py .

# Führe main.py aus, wenn der Container gestartet wird
CMD ["python", "main.py"]
# Stage 1: Build stage
FROM python:3.13-slim AS builder

# Arbeitsverzeichnis und Environment-Variablen
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Pip aktualisieren und Abhängigkeiten installieren
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Anwendungscode und Datenskripte kopieren & ausführen
COPY main.py ./
RUN python main.py

# ---------------------------
# Stage 2: Production stage
FROM python:3.13-slim

# Benutzer & Arbeitsverzeichnis anlegen
RUN useradd -m -r appuser && mkdir /app && chown -R appuser /app
WORKDIR /app

# Abhängigkeiten und Anwendung aus Builder-Stage kopieren
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /app/ /app/

# Environment-Variablen setzen
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Nicht-root User verwenden & Port freigeben
USER appuser
EXPOSE 8000

# Start mit Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "my_docker_django_app.wsgi:application"]
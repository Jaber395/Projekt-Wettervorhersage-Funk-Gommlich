from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import get_weather_data

def homepage(request):
    return render(request, "index.html")  # Lädt die Startseite aus templates/

urlpatterns = [
    path("admin/", admin.site.urls),  # Admin-Panel
    path("weather-data/", get_weather_data, name="weather_data"),
    path("", homepage, name="homepage"),  # Startseite
]

# Statische Dateien in DEBUG-Modus bereitstellen
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
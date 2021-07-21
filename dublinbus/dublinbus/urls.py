"""dublinbus URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from main import views as main_views
from main import api as main_api

urlpatterns = [
    path("", main_views.index, name="home"),
    path("realtime/", main_views.real_time, name="realtime"),
    path("busroutes/", main_views.bus_routes, name="busroutes"),
    path("api/get_bus_stops/", main_api.get_bus_stops, name="getbusstops"),
    path(
        "api/get_journey_travel_time_estimation/",
        main_api.get_journey_travel_time_estimation,
        name="gettraveltimes",
    ),
    path("admin/", admin.site.urls),
    path("api/weather_widget", main_api.weather_widget, name="weather_widget"),
    path("api/autocomple_route", main_api.autocomple_route, name="autocomple_route"),
]

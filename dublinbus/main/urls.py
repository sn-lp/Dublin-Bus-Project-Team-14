from django.urls import path
from . import views
from . import api
from . import cache_manipulator

urlpatterns = [
    path("", views.index, name="index"),
    path("realtime/", views.real_time, name="realtime"),
    path("busroutes/", views.bus_routes, name="busroutes"),
    path("api/get_bus_stops", api.get_bus_stops, name="getbusstops"),
    path("api/weather_widget", api.weather_widget, name="weather_widget"),
    path("api/autocomple_route", api.autocomple_route, name="autocomple_route"),
]

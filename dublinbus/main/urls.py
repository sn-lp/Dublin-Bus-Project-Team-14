from django.urls import path
from . import views
from . import api

urlpatterns = [
    path("", views.index, name="index"),
    path("realtime/", views.real_time, name="realtime"),
    path("busroutes/", views.bus_routes, name="busroutes"),
    path("api/get_bus_stops", api.get_bus_stops, name="getbusstops"),
]

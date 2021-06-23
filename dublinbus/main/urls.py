from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("realtime/", views.real_time, name="realtime"),
    path("busroutes/", views.bus_routes, name="busroutes"),
]

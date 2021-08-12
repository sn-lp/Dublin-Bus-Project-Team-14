from django.urls import path
from . import views
from . import api
from . import cache_manipulator

urlpatterns = [
    path("", views.index, name="index"),
    path("realtime/", views.real_time, name="realtime"),
    path("busroutes/", views.bus_routes, name="busroutes"),
    path("api/get_bus_stops", api.get_bus_stops, name="getbusstops"),
    path("api/get_all_bus_stops", api.get_all_bus_stops, name="getallbusstops"),
    path("api/weather_widget", api.weather_widget, name="weather_widget"),
    path("api/autocomple_route", api.autocomple_route, name="autocomple_route"),
    path("api/autocomple_stop", api.autocomple_stop, name="autocomple_stop"),
    path(
        "api/get_journey_travel_time_estimation",
        api.get_journey_travel_time_estimation,
        name="gettraveltimes",
    ),
    path("api/get_bus_stop_times", api.get_bus_stop_times, name="getbusstoptimes"),
    path("api/get_gtfsr_response/", api.get_gtfsr_response, name="getgtfsrresponse"),
    path(
        "api/quantile_dot_plot_request",
        api.quantile_dot_plot_request,
        name="quantile_dot_plot_request",
    ),
]

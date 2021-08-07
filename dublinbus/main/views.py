from django.conf import settings

from django.template import loader
from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    template = loader.get_template("main/index.html")
    if not settings.GOOGLE_MAPS_API_KEY:
        # if key is empty because it couldn't find the env variable, return an "Internal Server Error" 500 response code
        return HttpResponse(status=500)
    context = {"GOOGLEMAPS_APIKEY": settings.GOOGLE_MAPS_API_KEY}
    return HttpResponse(template.render(context, request))


def real_time(request):
    template = loader.get_template("main/realtime.html")
    if not settings.GOOGLE_MAPS_API_KEY:
        # if key is empty because it couldn't find the env variable, return an "Internal Server Error" 500 response code
        return HttpResponse(status=500)
    context = {
        "GOOGLEMAPS_APIKEY": settings.GOOGLE_MAPS_API_KEY,
    }
    return HttpResponse(template.render(context, request))


def bus_routes(request):
    template = loader.get_template("main/routes.html")
    if not settings.GOOGLE_MAPS_API_KEY:
        # if key is empty because it couldn't find the env variable, return an "Internal Server Error" 500 response code
        return HttpResponse(status=500)
    context = {"GOOGLEMAPS_APIKEY": settings.GOOGLE_MAPS_API_KEY}
    return HttpResponse(template.render(context, request))

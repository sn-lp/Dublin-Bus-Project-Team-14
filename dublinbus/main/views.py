from django.template import loader
from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    template = loader.get_template("main/index.html")
    context = {"title": "Dublin Bus Homepage", "team_number": 14}
    return HttpResponse(template.render(context, request))


def real_time(request):
    template = loader.get_template("main/realtime.html")
    context = {"title": "Dublin Bus Real time info page", "team_number": 14}
    return HttpResponse(template.render(context, request))


def bus_routes(request):
    template = loader.get_template("main/routes.html")
    context = {"title": "Dublin Bus routes page", "team_number": 14}
    return HttpResponse(template.render(context, request))

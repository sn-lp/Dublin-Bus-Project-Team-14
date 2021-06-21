from django.template import loader
from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    template = loader.get_template("main/index.html")
    context = {"title": "Dublin Bus Homepage", "team_number": 14}
    return HttpResponse(template.render(context, request))

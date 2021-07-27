from django.http import JsonResponse
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from main.models import Route, Trip, Trips_Stops, Stop
from main.cache_manipulator import *
import json

# returns all bus stops for each direction of each bus route
def get_bus_stops(request):
    # this endpoint receives the route number selected by the user through a query parameter sent by the frontend
    if "route_number" not in request.GET:
        return JsonResponse({"error": '"route_number" query parameter not found'})
    route_number = request.GET["route_number"]
    # routes_query_result is a list and each element in the list is a row in the routes table that has short_name equal to route_number
    routes_query_result = Route.objects.filter(short_name=route_number)
    if not routes_query_result:
        return JsonResponse({})
    # each "short_name" value in the routes table has two different "route_id" because they contain the same information
    # because of this we only need to select one "id" of the two that are returned
    route_id = routes_query_result[0].id

    # this query returns two trip_ids - one for each route direction
    # in the database each route direction has many different trip ids associated but with repeated headsigns and repeated bus stop information
    # getting two trip ids (one representing inbound trip and another representing outbound trip) is enough to get the two unique directions and corresponding bus stops
    trips_query_result = Trip.objects.filter(route_id=route_id).order_by("id")[:2]
    if not trips_query_result:
        return JsonResponse({})

    json_result = {}
    trip_ids = {}
    for result in trips_query_result:
        trip_ids[result.id] = result.headsign
        json_result[result.headsign] = {}

    # gets all bus stops for each of the two trip ids filtered above and adds data to the json_result dict returned by the function
    for id in trip_ids.keys():
        trips_stops_query_result = Trips_Stops.objects.filter(trip_id=id).values(
            "stop_id"
        )
        stops = Stop.objects.filter(id__in=trips_stops_query_result)
        for stop in stops:
            headsign = trip_ids[id]
            json_result[headsign][stop.name] = {
                "latitude": stop.latitude,
                "longitude": stop.longitude,
            }
    return JsonResponse(json_result)


def get_all_bus_stops(request):

    stops = Stop.objects.all()
    json_result = {}

    for stop in stops:
        json_result[stop.name] = {
            "latitude": stop.latitude,
            "longitude": stop.longitude,
        }
    return JsonResponse(json_result)


# Returns current weather data dictionary for building weather widget
def weather_widget(request):
    input_timestamp = datetime.now().timestamp()
    # need to add a few seconds to the input time so that it works with get_weather() function where it is comparing
    # "input_timestamp" with "current_timestamp" and if current is bigger than input it would return None
    # if we don't add the seconds, input will always be smaller since this is calculated before calling get_weather()
    input_timestamp += 5
    weather = get_weather(input_timestamp)
    return JsonResponse(weather.__dict__)


def autocomple_route(request):
    insert = request.GET.get("insert")
    routes = []
    if insert:
        route_objs = (
            Route.objects.filter(short_name__icontains=insert)
            .values("short_name")
            .distinct()
        )

        for route_obj in route_objs:
            routes.append(route_obj["short_name"])

    return JsonResponse({"status": 200, "data": routes})


# returns travel time estimations for all suggested routes
def get_journey_travel_time_estimation(request):
    # this endpoint receives a dictionary with departure date/time and route's data
    if request.method == "POST":
        routesData = json.loads(request.body)
        # TODO access routes' data and format any data if necessary according to the data format the models were trained on
        datetime_object = datetime.strptime(routesData["departure_time"], '%Y-%m-%dT%H:%M')
        hour_of_the_day = datetime_object.hour
        day_of_the_week = datetime_object.weekday()
        month_of_the_year = datetime_object.month
        # TODO feed data to models and get estimated travel time
        # TODO calculate total time, if needed by combining our Dublin Bus predictions with other times from other steps that are not operated by Dublin Bus
        # TODO send total times for all suggested routes to frontend that will render them by replacing the times injected from the google directions api response
        return JsonResponse({})

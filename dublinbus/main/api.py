from django.http import JsonResponse
from main.models import Route, Trip, Trips_Stops, Stop
from main.cache_manipulator import *

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

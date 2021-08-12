from django.http import JsonResponse
from django.http.response import HttpResponse
from main.models import Route, Trip, Trips_Stops, Stop, Stop_Times
from main.cache_manipulator import *
import json
from django.db import connection
import os.path
from django.db.models import Q
import pandas as pd
import joblib
from datetime import timedelta
import time
import os
from django.core.files.storage import default_storage as bucketStorage


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


def get_bus_stop_times(request):
    # Will only return values which are within the next 1 hour.

    if "stop_id" not in request.GET:
        return JsonResponse({"error": '"stop_id" query parameter not found'})
    requested_stop_id = request.GET["stop_id"]

    now = datetime.now()
    hour_ahead = now + timedelta(hours=1)

    current_time = now.strftime("%H:%M:%S")
    current_time_1hr = hour_ahead.strftime("%H:%M:%S")

    stop_times = Stop_Times.objects.filter(
        stop_id=requested_stop_id,
        arrival_time__gte=current_time,
        arrival_time__lte=current_time_1hr,
    )
    json_result = {}

    day_of_week = datetime.today().weekday()
    service_id_dict = {
        "y1007": [0, 1, 2, 3, 4],
        "y1008": [6],
        "y1009": [5],
    }

    for stop_time in stop_times:
        service_id = stop_time.trip_id.split(".")[1]
        if day_of_week in service_id_dict[service_id]:

            json_result[stop_time.id] = {
                "arrival_time": stop_time.arrival_time,
                "trip_id": stop_time.trip_id,
                "stop_id": stop_time.stop_id,
            }

    return JsonResponse(json_result)


def get_all_bus_stops(request):

    json_result = {}

    if "stop_name" in request.GET:
        stop_name = request.GET["stop_name"]
        stops = Stop.objects.filter(name=stop_name)

        for stop in stops:
            json_result[stop.name] = {
                "latitude": stop.latitude,
                "longitude": stop.longitude,
                "id": stop.id,
            }

        return JsonResponse(json_result)

    stops = Stop.objects.all()

    for stop in stops:
        json_result[stop.name] = {
            "latitude": stop.latitude,
            "longitude": stop.longitude,
            "id": stop.id,
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

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM (SELECT concat(a.short_name, ' - ', b.headsign) AS new_name FROM routes as a RIGHT JOIN trips AS b ON a.id = b.route_id Group By short_name) c "
            + "WHERE c.new_name like %s;",
            ["%" + str(insert) + "%"],
        )
        rows = cursor.fetchall()
        for row in rows:
            routes.append(row)

    return JsonResponse({"status": 200, "data": routes})


def autocomple_stop(request):
    insert = request.GET.get("insert")
    stops = []
    if insert:
        stop_objs = (
            Stop.objects.filter(name__icontains=insert).values("name").distinct()
        )

        for route_obj in stop_objs:
            stops.append(route_obj["name"])

    return JsonResponse({"status": 200, "data": stops})


def model_prediction(
    route, progress_number, direction, day, month, temp, weather, hour
):
    route_model_file = f"ml_models/KNN_models/knn_{route}.joblib"
    with bucketStorage.open(route_model_file, "rb") as f:
        route_model = joblib.load(f)
    # convert the data to a list of parameters for the predictive KNN model

    # index     0     1       2    3      4     5       6        7    8     9     10     11    12
    # feature  prog, direct, day, month, temp, clouds, drizzle, fog, mist, rain, smoke, snow, hour
    model_args = [0] * 13
    model_args[0] = progress_number
    model_args[1] = direction
    model_args[2] = day
    model_args[3] = month
    model_args[4] = temp

    if weather == "Clouds":
        model_args[5] = 1
    elif weather == "Drizzle":
        model_args[6] = 1
    elif weather == "Fog":
        model_args[7] = 1
    elif weather == "Mist":
        model_args[8] = 1
    elif weather == "Rain" or weather == "Thunderstorm":
        model_args[9] = 1
    elif (
        weather == "Smoke"
        or weather == "Haze"
        or weather == "Dust"
        or weather == "Sand"
        or weather == "Ash"
    ):
        model_args[10] = 1
    elif weather == "Snow":
        model_args[11] = 1

    model_args[12] = hour

    return float(
        route_model.predict(
            pd.DataFrame(
                [model_args],
                columns=[
                    "PROGRNUMBER",
                    "DIRECTION",
                    "DAYOFWEEK",
                    "MONTHOFYEAR",
                    "temp",
                    "w_main_Clouds",
                    "w_main_Drizzle",
                    "w_main_Fog",
                    "w_main_Mist",
                    "w_main_Rain",
                    "w_main_Smoke",
                    "w_main_Snow",
                    "HOUROFDAY",
                ],
            )
        )
    )


# returns travel time estimations for all suggested routes
def get_journey_travel_time_estimation(request):
    if not request.method == "POST":
        return JsonResponse({"error": "endpoint only accepts POST requests"})

    try:
        # this endpoint receives a dictionary with departure date/time and route's data
        routesData = json.loads(request.body)
    except:
        return JsonResponse({"error": "request.body cannot be parsed as a JSON object"})

    if not "routesData" in routesData and not "departureTime" in routesData:
        return JsonResponse(
            {"error": "JSON object must have 'routesData' and 'departureTime'"}
        )

    # the time selected by the user in the calendar form
    user_datetime_object = datetime.strptime(
        routesData["departureTime"], "%Y-%m-%dT%H:%M"
    )

    # initialise empty dict that will have the predictions for all routes to send to frontend
    routes_predictions = {}
    for i in range(0, len(routesData["routesData"])):
        routes_predictions[f"route_{i}"] = _get_travel_time_for_route(
            routesData["routesData"][i], user_datetime_object
        )

    return JsonResponse(routes_predictions)


# receives a route and returns route travel time estimation
def _get_travel_time_for_route(route, user_datetime_object):
    route_travel_prediction = {}

    route_start_time = route[0]["start_time"]
    # convert start time to datetime object
    # this line will remove from the string the timezone description within parenthesis, e.g. 'Fri Aug 06 2021 11:39:36 GMT+0100 (Irish Standard Time)'
    start_time_without_description = route_start_time.split(" (", 1)[0]
    # after the description of timezone is removed we can convert to a datetime object
    start_time_datetime_object = datetime.strptime(
        start_time_without_description, f"%a %b %d %Y %H:%M:%S %Z%z"
    )
    route_travel_prediction["journey_starts"] = _datetime_to_hour_minutes_string(
        start_time_datetime_object
    )

    # route_total_time is in seconds and holds total amount of seconds the route takes
    route_total_time = 0
    # iterate through the steps and skip the start time dict which is the first element of each route's list
    step_index = 0
    # summing step duration to elapsed_time will give the start and end clock time of a step
    elapsed_time = start_time_datetime_object
    for route_step_dict in route[1:]:
        (
            step_time_estimation,
            step_number_of_stops,
            step_starts,
            step_ends,
            step_duration,
        ) = _get_step_time_estimation(
            route_step_dict, user_datetime_object, elapsed_time
        )
        route_total_time += step_time_estimation

        route_travel_prediction[f"step_{step_index}"] = {
            "number_of_stops": step_number_of_stops,
            "step_starts": step_starts,
            "step_ends": step_ends,
            "step_duration": step_duration,
        }
        elapsed_time += timedelta(seconds=step_time_estimation)
        step_index += 1

    total_seconds = timedelta(seconds=route_total_time)
    end_time_datetime_object = start_time_datetime_object + total_seconds
    # convert route total time in seconds to string with hours and mins to send to frontend already formatted
    route_duration = _convert_number_of_seconds_to_time_string(route_total_time)
    # add total time in seconds we estimate the route will take to the routes predictions dict
    route_travel_prediction["route_duration"] = route_duration

    # add final clock time of the journey to the routes_predictions dict
    route_travel_prediction["journey_ends"] = _datetime_to_hour_minutes_string(
        end_time_datetime_object
    )

    return route_travel_prediction


def _get_step_time_estimation(route_step_dict, user_datetime_object, elapsed_time):
    step_time_estimation = 0
    step_number_of_stops = 0
    step_starts = ""
    step_ends = ""
    step_duration = ""

    if not "step" in route_step_dict or not "step_duration" in route_step_dict["step"]:
        return (
            step_time_estimation,
            step_number_of_stops,
            step_starts,
            step_ends,
            step_duration,
        )

    google_travel_time_prediction = route_step_dict["step"]["step_duration"]

    # walking steps and some other bus providers don't have number_of_stops
    if "number_of_stops" in route_step_dict["step"]:
        step_number_of_stops = route_step_dict["step"]["number_of_stops"]

    # if it is the first step of a route than it will have the same start time as the route itself
    # since at first elapsed_time will be the same as the journey start time
    step_starts = _datetime_to_hour_minutes_string(elapsed_time)

    if "departure_time" in route_step_dict["step"]:
        # use google's step's departure time to feed the date, time and weather to the models
        departure_time = route_step_dict["step"]["departure_time"]
        departure_time_without_description = departure_time.split(" (", 1)[0]
        departure_time_datetime_object = datetime.strptime(
            departure_time_without_description, f"%a %b %d %Y %H:%M:%S %Z%z"
        )
        day = departure_time_datetime_object.weekday()
        month = departure_time_datetime_object.month
        hour = departure_time_datetime_object.hour
        weather = get_weather(departure_time_datetime_object.timestamp())
    else:
        # use user selected date and time
        day = user_datetime_object.weekday()
        month = user_datetime_object.month
        hour = user_datetime_object.hour
        weather = get_weather(user_datetime_object.timestamp())

    weather_main = weather.get_weather_main()
    temp = weather.get_temp()

    if (
        route_step_dict["step"]["travel_mode"] == "WALKING"
        or route_step_dict["step"]["provider"] != "Dublin Bus"
    ):
        step_time_estimation += google_travel_time_prediction
        elapsed_time += timedelta(seconds=step_time_estimation)
        step_ends = _datetime_to_hour_minutes_string(elapsed_time)
        step_duration = _convert_number_of_seconds_to_time_string(step_time_estimation)
        return (
            step_time_estimation,
            step_number_of_stops,
            step_starts,
            step_ends,
            step_duration,
        )
    else:
        route_shortname = route_step_dict["step"]["bus_line_short_name"]
        matching_route_in_db = Route.objects.filter(short_name=route_shortname.lower())
        if not matching_route_in_db or not bucketStorage.exists(
            f"ml_models/KNN_models/knn_{route_shortname}.joblib"
        ):
            step_time_estimation += google_travel_time_prediction
            elapsed_time += timedelta(seconds=step_time_estimation)
            step_ends = _datetime_to_hour_minutes_string(elapsed_time)
            step_duration = _convert_number_of_seconds_to_time_string(
                step_time_estimation
            )
            return (
                step_time_estimation,
                step_number_of_stops,
                step_starts,
                step_ends,
                step_duration,
            )

        trip_headsign = route_step_dict["step"]["bus_line_long_name"]
        departure_stop = route_step_dict["step"]["departure_stop"]
        arrival_stop = route_step_dict["step"]["arrival_stop"]
        # we will get these variable's values from database if we find route matching data
        bus_direction = 0
        departure_stop_progress_number = 0
        arrival_stop_progress_number = 0

        # check if there's matching trip an bus stops in the DB to get progress numbers and trip direction
        for route in matching_route_in_db:
            matching_trip = Trip.objects.filter(
                Q(headsign=trip_headsign) & Q(route_id=route.id)
            ).first()
            if matching_trip:
                bus_direction = matching_trip.direction
                break
        # bus direction must be 1 or 2 in case we have a matching trip in the database
        if bus_direction == 0:
            step_time_estimation += google_travel_time_prediction
            step_duration = _convert_number_of_seconds_to_time_string(
                step_time_estimation
            )
            return (
                step_time_estimation,
                step_number_of_stops,
                step_starts,
                step_ends,
                step_duration,
            )

        trip_id = matching_trip.id
        matching_departure_stop = Stop.objects.filter(Q(name=departure_stop)).first()
        if matching_departure_stop:
            departure_trip_stop = Trips_Stops.objects.filter(
                Q(trip_id=trip_id) & Q(stop_id=matching_departure_stop.id)
            ).first()
            if departure_trip_stop:
                departure_stop_progress_number = departure_trip_stop.progress_number

        # progress numbers must be bigger than 0 in case we have a matching stop in the database
        if departure_stop_progress_number == 0:
            step_time_estimation += google_travel_time_prediction
            elapsed_time += timedelta(seconds=step_time_estimation)
            step_ends = _datetime_to_hour_minutes_string(elapsed_time)
            step_duration = _convert_number_of_seconds_to_time_string(
                step_time_estimation
            )
            return (
                step_time_estimation,
                step_number_of_stops,
                step_starts,
                step_ends,
                step_duration,
            )

        matching_arrival_stop = Stop.objects.filter(Q(name=arrival_stop)).first()
        if matching_arrival_stop:
            arrival_trip_stop = Trips_Stops.objects.filter(
                Q(trip_id=trip_id) & Q(stop_id=matching_arrival_stop.id)
            ).first()
            if arrival_trip_stop:
                arrival_stop_progress_number = arrival_trip_stop.progress_number

        if arrival_stop_progress_number == 0:
            step_time_estimation += google_travel_time_prediction
            elapsed_time += timedelta(seconds=step_time_estimation)
            step_ends = _datetime_to_hour_minutes_string(elapsed_time)
            step_duration = _convert_number_of_seconds_to_time_string(
                step_time_estimation
            )
            return (
                step_time_estimation,
                step_number_of_stops,
                step_starts,
                step_ends,
                step_duration,
            )

        # make predictions if all necessary values are available
        departure_stop_prediction = model_prediction(
            route_shortname,
            departure_stop_progress_number,
            bus_direction,
            day,
            month,
            temp,
            weather_main,
            hour,
        )
        arrival_stop_prediction = model_prediction(
            route_shortname,
            arrival_stop_progress_number,
            bus_direction,
            day,
            month,
            temp,
            weather_main,
            hour,
        )
        step_travel_time_prediction = (
            arrival_stop_prediction - departure_stop_prediction
        )
        step_time_estimation += step_travel_time_prediction
        elapsed_time += timedelta(seconds=step_time_estimation)
        step_ends = _datetime_to_hour_minutes_string(elapsed_time)
        step_duration = _convert_number_of_seconds_to_time_string(step_time_estimation)
        return (
            step_time_estimation,
            step_number_of_stops,
            step_starts,
            step_ends,
            step_duration,
        )


# returns a string from a datetime in a format 'hh:mm'
# datetime.minute gives an int in range(60), if minute < than 10 we need to add one zero to the string before the int returned
def _datetime_to_hour_minutes_string(datetime):
    if datetime.minute < 10:
        return f"{datetime.hour}:0{datetime.minute}"
    else:
        return f"{datetime.hour}:{datetime.minute}"


def _convert_number_of_seconds_to_time_string(seconds):
    if os.name == "nt":
        time_format_os_specific = "#"
    else:
        time_format_os_specific = "-"
    if seconds > 3600:
        if seconds < 7200:
            time_string = time.strftime(
                f"%{time_format_os_specific}H hour %{time_format_os_specific}M mins",
                time.gmtime(seconds),
            )
        else:
            time_string = time.strftime(
                f"%{time_format_os_specific}H hours %{time_format_os_specific}M mins",
                time.gmtime(seconds),
            )
    else:
        time_string = time.strftime(
            f"%{time_format_os_specific}M mins", time.gmtime(seconds)
        )
    return time_string

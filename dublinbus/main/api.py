import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from io import BytesIO
import base64

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
import requests
from django.conf import settings
from django.core.files.storage import default_storage as bucketStorage
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.collections import PatchCollection
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
from statistics import variance
from scipy.stats import lognorm


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
            step_estimated_cost,
            route_name,
            predicted_by_app,
        ) = _get_step_time_estimation(
            route_step_dict, user_datetime_object, elapsed_time
        )
        route_total_time += step_time_estimation

        route_travel_prediction[f"step_{step_index}"] = {
            "number_of_stops": step_number_of_stops,
            "step_starts": step_starts,
            "step_ends": step_ends,
            "step_duration": step_duration,
            "prediction_in_seconds": step_time_estimation,
            "step_cost": step_estimated_cost,
            "route_name": route_name,
            "predicted_by_app": predicted_by_app,
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
    step_estimated_cost = ""
    route_name = ""
    predicted_by_app = False

    if not "step" in route_step_dict or not "step_duration" in route_step_dict["step"]:
        return (
            step_time_estimation,
            step_number_of_stops,
            step_starts,
            step_ends,
            step_duration,
            step_estimated_cost,
            route_name,
            predicted_by_app,
        )

    google_travel_time_prediction = route_step_dict["step"]["step_duration"]

    # walking steps and some other bus providers don't have number_of_stops
    if "number_of_stops" in route_step_dict["step"]:
        step_number_of_stops = route_step_dict["step"]["number_of_stops"]

    # if it is the first step of a route than it will have the same start time as the route itself
    # since at first elapsed_time will be the same as the journey start time
    step_starts = _datetime_to_hour_minutes_string(elapsed_time)

    # calculate estimated cost of step if it is using a Dublin Bus bus
    if "provider" in route_step_dict["step"]:
        if route_step_dict["step"]["provider"] == "Dublin Bus":
            step_estimated_cost = _calculate_step_cost(
                route_step_dict["step"]["number_of_stops"]
            )
            if "bus_line_short_name" in route_step_dict["step"]:
                route_name = route_step_dict["step"]["bus_line_short_name"]

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
            step_estimated_cost,
            route_name,
            predicted_by_app,
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
                step_estimated_cost,
                route_name,
                predicted_by_app,
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
                step_estimated_cost,
                route_name,
                predicted_by_app,
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
                step_estimated_cost,
                route_name,
                predicted_by_app,
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
                step_estimated_cost,
                route_name,
                predicted_by_app,
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
        predicted_by_app = True
        return (
            step_time_estimation,
            step_number_of_stops,
            step_starts,
            step_ends,
            step_duration,
            step_estimated_cost,
            route_name,
            predicted_by_app,
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


# this function uses bus fares calculations from https://www.transportforireland.ie/fares/bus-fares/
def _calculate_step_cost(number_of_stops):
    if number_of_stops <= 3:
        adult_leap_cost = "€1.55"
    elif number_of_stops <= 13:
        adult_leap_cost = "€2.25"
    else:
        adult_leap_cost = "€2.50"
    return adult_leap_cost


def get_gtfsr_response(request):
    cache_res = get_last_gtfsr_response()
    if cache_res is not None:
        return JsonResponse(cache_res)

    url = "https://gtfsr.transportforireland.ie/v1/?format=json"
    headers_dic = {
        "Cache-Control": "no-cache",
        "x-api-key": settings.GTFSR_APIKEY,
    }

    with requests.get(url, headers=headers_dic) as response:
        try:
            # even if the response status is not 200, we still need to keep it in cache for two reasons:
            # 1. revealing the actual error message will make it easier to debug
            # 2. have something in cache, so the function caller have to cool down for 1 minute
            update_gtfsr_response(json.loads(response.content))
        except:
            # can add a log here, when we have log functionality
            pass

    # failure could be caused by both http connection or json conversion, so the following statement cannot be put in json's try-except only
    # no matter what made the previous process failed, we still need to have a record in cache
    # for telling the function caller to cool down for 1 minute
    if get_last_gtfsr_response() is None:
        update_gtfsr_response(
            {
                "statusCode": 500,
                "message": "there was something wrong with gtfr, please cool down, and wait for one minute.",
            }
        )

    return JsonResponse(get_last_gtfsr_response())


# code adapted from https://gist.github.com/tupui/c8dd181fd1e732584bbd7109b96177e3
# function to plot quantile dot plot given the normalised data and model prediction
def quantile_dotplot_generator(request):

    if "line_id" not in request.GET:
        return JsonResponse({"error": '"line_id" query parameter not found'})
    lineid = request.GET["line_id"]

    if "prediction" not in request.GET:
        return JsonResponse({"error": '"prediction" query parameter not found'})
    pred = request.GET["prediction"]

    # Conversion needed as predictions are given in seconds, while this function uses minutes.
    pred = int(float(pred)) / 60

    linedist = pd.read_csv("main/knn_dist_csvs/knn_dist_{}".format(lineid), header=None)
    normdata = linedist[0].to_list()

    sample = 20
    p_less_than_x = np.linspace(1 / sample / 2, 1 - (1 / sample / 2), sample)

    # scaling up the data and shifting it with the prediction
    preddata = []
    for i in normdata:
        preddata += [i * pred + pred]

    # getting standard deviation and mean of the new data
    stdev = variance(preddata) ** 0.5
    sum = 0
    for j in preddata:
        sum += j
    mean = sum / len(preddata)

    # probability density function
    pdf = lognorm.pdf

    # applying the inverse CDF to our new data
    x2 = np.percentile(preddata, p_less_than_x * 100)  # Inverce CDF (ppf)

    # Create bins
    n_bins = 7
    hist = np.histogram(x2, bins=n_bins)
    bins, edges = hist
    radius = (edges[1] - edges[0]) / 2

    fig, ax = plt.subplots()
    ax.set_xlabel("Minutes")

    # Dotplot
    ax2 = ax.twinx()
    patches = []
    max_y = 0
    max_len = 0
    for i in range(n_bins):
        x_bin = (edges[i + 1] + edges[i]) / 2
        y_bins = [(i + 1) * (radius * 2) for i in range(bins[i])]

        # if y_bins is empty, continue
        if not y_bins:
            continue

        if len(y_bins) > max_len:
            max_len = len(y_bins)

        max_y = max(y_bins) if max(y_bins) > max_y else max_y

        for _, y_bin in enumerate(y_bins):
            circle = Circle((x_bin, y_bin), radius)
            patches.append(circle)

    # putting the circles together, setting colour
    p = PatchCollection(patches, alpha=0.4)
    p.set_facecolor("royalblue")
    ax2.add_collection(p)

    # dictionary for scale factors
    scale_dict = {
        "68": 1.6,
        "45A": 1.4,
        "25A": 1.5,
        "14": 1.7,
        "77A": 1.25,
        "39": 1.4,
        "16": 1.2,
        "40D": 1.2,
        "27B": 1.35,
        "142": 1.1,
        "83": 1.3,
        "130": 1,
        "15": 1.6,
        "46A": 1.3,
        "33": 1.4,
        "7": 1.5,
        "39A": 1.5,
        "1": 1.3,
        "41": 1.2,
        "67X": 1.1,
        "59": 1.3,
        "9": 1.5,
        "40": 1.6,
        "239": 1.6,
        "84": 1.1,
        "53": 1.1,
        "185": 0.7,
        "151": 1.3,
        "13": 1.35,
        "15B": 1.3,
        "65B": 1.1,
        "29A": 1.6,
        "61": 1,
        "140": 7.2,
        "123": 1.3,
        "79A": 1,
        "38A": 1.5,
        "31": 1,
        "69": 1.35,
        "44": 1.6,
        "42": 2.2,
        "67": 1.3,
        "184": 1.4,
        "238": 1,
        "145": 1.45,
        "17A": 1.6,
        "32": 1.5,
        "27A": 1.3,
        "17": 1.4,
        "27X": 1.5,
        "122": 1.45,
        "54A": 1.3,
        "66": 1.6,
        "150": 1.2,
        "56A": 1.3,
        "37": 1.5,
        "27": 1.6,
        "15A": 1,
        "65": 1.3,
        "47": 1.6,
        "76": 1.45,
        "79": 1.15,
        "83A": 1.4,
        "63": 1.5,
        "33B": 0.9,
        "4": 1.35,
        "120": 1.6,
        "41C": 1.45,
        "70": 1.2,
        "84A": 1.5,
        "220": 1.45,
        "32X": 1.45,
        "68A": 1,
        "84X": 0.7,
        "38": 1.35,
        "102": 1.6,
        "270": 1.4,
        "51X": 1,
        "33X": 1.6,
        "75": 1.35,
        "26": 1.5,
        "66A": 1.3,
        "31A": 1,
        "49": 1.2,
        "111": 0.8,
        "18": 1.3,
        "11": 1.5,
        "14C": 1.4,
        "114": 1.4,
        "76A": 1.1,
        "44B": 1.5,
        "7A": 1.6,
        "43": 1.3,
        "25": 1.6,
        "104": 1.6,
        "33A": 1.1,
        "16C": 1.3,
        "42D": 1.1,
        "31B": 0.8,
        "66X": 1,
        "31D": 1.6,
        "33D": 1.6,
        "39X": 1.7,
        "41B": 1.45,
        "25B": 1.2,
        "7D": 1.4,
        "46E": 1.6,
        "118": 0.8,
        "51D": 1.8,
        "15D": 1.4,
        "41A": 1.6,
        "25D": 1.1,
        "38D": 1.2,
        "40B": 1.6,
        "66B": 1.4,
        "38B": 1.6,
        "236": 0.7,
        "7B": 1.45,
        "41X": 0.8,
        "40E": 1.4,
        "161": 1,
        "70D": 1.4,
        "69X": 1.6,
        "116": 1.6,
        "77X": 1.6,
        "25X": 1.6,
        "68X": 1.5,
        "16D": 1.4,
        "33E": 1.5,
        "41D": 2.3,
    }

    scale = scale_dict[lineid]

    # dictionary for the shift factor
    shift_dict = {
        "68": 0.08,
        "45A": -0.1,
        "25A": -0.02,
        "14": 0.06,
        "77A": -0.15,
        "39": 0.05,
        "16": -0.15,
        "40D": -0.2,
        "27B": -0.1,
        "142": -0.22,
        "83": -0.05,
        "130": -0.35,
        "15": 0,
        "46A": -0.05,
        "33": 0.02,
        "7": 0.02,
        "39A": 0.02,
        "1": -0.2,
        "41": -0.1,
        "67X": -0.3,
        "59": -0.17,
        "9": 0,
        "40": 0,
        "239": 0.05,
        "84": -0.15,
        "53": -0.12,
        "185": -0.45,
        "151": -0.07,
        "13": -0.07,
        "15B": 0,
        "65B": -0.1,
        "29A": 0.02,
        "61": -0.11,
        "140": 0.57,
        "123": -0.06,
        "79A": -0.2,
        "38A": 0,
        "31": 0,
        "69": 0.03,
        "44": -0.02,
        "42": 0.22,
        "67": 0,
        "184": -0.1,
        "238": -0.23,
        "145": -0.02,
        "17A": 0.1,
        "32": 0,
        "27A": -0.1,
        "17": 0,
        "27X": -0.1,
        "122": 0,
        "54A": -0.13,
        "66": 0.02,
        "150": 0,
        "56A": 0,
        "37": 0.05,
        "27": 0,
        "15A": 0,
        "65": 0,
        "47": 0.03,
        "76": 0.05,
        "79": -0.1,
        "83A": -0.2,
        "63": 0,
        "33B": 0,
        "4": -0.03,
        "120": 0,
        "41C": 0.03,
        "70": -0.03,
        "84A": 0.01,
        "220": -0.04,
        "32X": -0.08,
        "68A": -0.16,
        "84X": -0.7,
        "38": 0,
        "102": 0.1,
        "270": 0.05,
        "51X": -0.23,
        "33X": 0.06,
        "75": -0.1,
        "26": 0,
        "66A": 0,
        "31A": -0.25,
        "49": -0.1,
        "111": -0.4,
        "18": -0.1,
        "11": 0,
        "14C": -0.18,
        "114": -0.16,
        "76A": -0.27,
        "44B": -0.1,
        "7A": 0.05,
        "43": -0.15,
        "25": 0.07,
        "104": 0,
        "33A": -0.25,
        "16C": 0,
        "42D": -0.15,
        "31B": -0.6,
        "66X": -0.3,
        "31D": 0,
        "33D": 0,
        "39X": 0.03,
        "41B": 0,
        "25B": -0.15,
        "7D": -0.1,
        "46E": 0,
        "118": -0.65,
        "51D": 0.02,
        "15D": -0.18,
        "41A": -0.04,
        "25D": -0.07,
        "38D": -0.22,
        "40B": 0.1,
        "66B": -0.13,
        "38B": 0,
        "236": -0.8,
        "7B": -0.03,
        "41X": -0.5,
        "40E": -0.12,
        "161": 0,
        "70D": -0.1,
        "69X": -0.02,
        "116": 0.07,
        "77X": -0.07,
        "25X": -0.02,
        "68X": -0.12,
        "16D": -0.15,
        "33E": -0.1,
        "41D": 0.25,
    }

    shift = shift_dict[lineid]

    # window size the same as a normal distribution with the same data, scale determines window size, shift determines
    # where it looks
    x1 = np.linspace(
        (mean - 3 * stdev) / scale + 0.45 * pred + shift * pred,
        (mean + 3 * stdev) / scale + 0.45 * pred + shift * pred,
        100,
    )

    # Axis tweak
    # arguments for lognorm function
    args = {"s": 0.2, "scale": 11.4}
    y_scale = (max_y + radius) / max(pdf(x1, **args))
    ticks_y = ticker.FuncFormatter(lambda x1, pos: "{0:g}".format(x1 / y_scale))
    ax2.yaxis.set_major_formatter(ticks_y)
    ax2.set_yticklabels([])
    ax2.set_xlim([min(x1) - radius, max(x1) + radius])
    ax2.set_ylim([0, max_y + radius])
    ax2.set_aspect(1)

    # turn off y ticks
    plt.yticks([])
    ax.yaxis.set_major_locator(plt.NullLocator())

    # adding more x ticks
    ax.xaxis.set_minor_locator(plt.MultipleLocator(1))

    # adding vertical line for the mean
    plt.axvline(x=pred, color="r")

    # Sendign image data as as base64 data (https://deeplearning.lipingyang.org/2018/07/21/django-sending-matplotlib-generated-figure-to-django-web-app/)
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=300)
    image_base64 = base64.b64encode(buf.getvalue()).decode("utf-8").replace("\n", "")
    buf.close()

    jsonResult = {"image_base64": image_base64}

    return JsonResponse(jsonResult)

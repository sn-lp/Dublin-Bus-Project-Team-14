from django.urls import reverse
from django.test import TestCase, Client
from main.cache_manipulator import get_weather
from datetime import datetime
import pytz
from main.models import Route, Trip, Trips_Stops, Stop, Stop_Times, Stop_Times
import json
from django.core.files.storage import default_storage as bucketStorage
import joblib
from main.api import (
    _get_travel_time_for_route,
    _get_step_time_estimation,
    _convert_number_of_seconds_to_time_string,
    _datetime_to_hour_minutes_string,
    _calculate_step_cost,
)
from datetime import timedelta
from main.cache_manipulator import *
import main.api


class AwsS3BucketTest(TestCase):
    def test_loading_predictive_model(self):
        with bucketStorage.open("ml_models/KNN_models/knn_1.joblib", "rb") as f:
            route_model = joblib.load(f)
        self.assertTrue(bucketStorage.exists("ml_models/"))
        self.assertTrue(route_model is not None)


class ViewTests(TestCase):
    def test_index_view(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_real_time_view(self):
        response = self.client.get(reverse("realtime"))
        self.assertEqual(response.status_code, 200)

    def test_routes_view(self):
        response = self.client.get(reverse("busroutes"))
        self.assertEqual(response.status_code, 200)


class CacheTests(TestCase):
    def test_get_weather(self):
        current_timestamp = datetime.now().timestamp()

        # out of range
        before_1min_timestamp = current_timestamp - 60
        in_8day_timestamp = current_timestamp + 8 * 24 * 60 * 60

        # in the hourly data range
        in_30min_timestamp = current_timestamp + 30 * 60
        in_12hr_timestamp = current_timestamp + 12 * 60 * 60
        in_47hr_timestamp = current_timestamp + 47 * 60 * 60

        # in the daily data range
        in_48hr_timestamp = current_timestamp + 2 * 24 * 60 * 60
        in_3day_timestamp = current_timestamp + 3 * 24 * 60 * 60
        in_7day_timestamp = current_timestamp + 7 * 24 * 60 * 60

        # truncate functions
        def truncate_hourly_time(timestamp):
            dt = datetime.fromtimestamp(timestamp, tz=pytz.timezone("Europe/Dublin"))
            return dt.replace(minute=0, second=0, microsecond=0).timestamp()

        def truncate_daily_time(timestamp):
            dt = datetime.fromtimestamp(timestamp, tz=pytz.timezone("Europe/Dublin"))
            return dt.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()

        # assertion:  (timestamp stored by the scraper in the cache) VS. (truncated orinignal timestamp)

        self.assertEqual(
            get_weather(in_30min_timestamp).get_timestamp(),
            truncate_hourly_time(in_30min_timestamp),
        )
        self.assertEqual(
            get_weather(in_12hr_timestamp).get_timestamp(),
            truncate_hourly_time(in_12hr_timestamp),
        )
        self.assertEqual(
            get_weather(in_47hr_timestamp).get_timestamp(),
            truncate_hourly_time(in_47hr_timestamp),
        )

        self.assertEqual(
            truncate_daily_time(get_weather(in_48hr_timestamp).get_timestamp()),
            truncate_daily_time(in_48hr_timestamp),
        )
        self.assertEqual(
            truncate_daily_time(get_weather(in_3day_timestamp).get_timestamp()),
            truncate_daily_time(in_3day_timestamp),
        )
        self.assertEqual(
            truncate_daily_time(get_weather(in_7day_timestamp).get_timestamp()),
            truncate_daily_time(in_7day_timestamp),
        )
        self.assertEqual(get_weather(in_8day_timestamp), None)


def setupTestData():
    # set up a simplified dataset for route 44
    Route.objects.create(id="60-44-d12-1", short_name="44")
    Trip.objects.create(
        id="10490.y1006.60-44-d12-1.245.O",
        route=Route.objects.filter(id="60-44-d12-1")[0],
        headsign="The Helix - Enniskerry Village",
    )
    Stop.objects.create(
        id="8220DB000044",
        name="Skylon Hotel, stop 44",
        latitude="53.373017409122895",
        longitude="-6.2521323032429095",
    )
    Stop.objects.create(
        id="8220DB000045",
        name="DCU St Patrick's, stop 45",
        latitude="53.36993643440311",
        longitude="-6.254106940849611",
    )
    Stop.objects.create(
        id="8220DB000046",
        name="Botanic Avenue, stop 46",
        latitude="53.367131016217606",
        longitude="-6.255258556550079",
    )
    Trips_Stops.objects.create(
        stop=Stop.objects.filter(id="8220DB000044")[0],
        trip=Trip.objects.filter(id="10490.y1006.60-44-d12-1.245.O")[0],
    )
    Trips_Stops.objects.create(
        stop=Stop.objects.filter(id="8220DB000045")[0],
        trip=Trip.objects.filter(id="10490.y1006.60-44-d12-1.245.O")[0],
    )
    Trips_Stops.objects.create(
        stop=Stop.objects.filter(id="8220DB000046")[0],
        trip=Trip.objects.filter(id="10490.y1006.60-44-d12-1.245.O")[0],
    )

    # To keep the test avaible for every day and every hour, I create only "one trip" for every hour every day
    trip_day_type = ["y1007", "y1008", "y1009"]
    count = 0
    for i in range(0, 24):
        for day in trip_day_type:
            Stop_Times.objects.create(
                trip_id="7712." + day + ".60-1-d12-1.1.O",
                arrival_time=str(i) + ":00:10",
                stop_id="8220DB000044",
                id=count,
            )
            count += 1

    # set up a simplified dataset for route 44b
    Route.objects.create(id="60-44B-b12-1", short_name="44b")
    Trip.objects.create(
        id="3527.y1003.60-44B-b12-1.239.O",
        route=Route.objects.filter(id="60-44B-b12-1")[0],
        headsign="Outside Luas Station - Hill View",
    )
    Stop.objects.create(
        id="8250DB002829",
        name="Balally Drive, stop 2829",
        latitude="53.2843852487127",
        longitude="-6.2368693911913",
    )
    Stop.objects.create(
        id="8250DB002830",
        name="Dun Emer Road, stop 2830",
        latitude="53.282359124655706",
        longitude="-6.23357835491192",
    )
    Stop.objects.create(
        id="8250DB002831",
        name="Balally Hill, stop 2831",
        latitude="53.2790576327384",
        longitude="-6.2315700334981",
    )
    Trips_Stops.objects.create(
        stop=Stop.objects.filter(id="8250DB002829")[0],
        trip=Trip.objects.filter(id="3527.y1003.60-44B-b12-1.239.O")[0],
    )
    Trips_Stops.objects.create(
        stop=Stop.objects.filter(id="8250DB002830")[0],
        trip=Trip.objects.filter(id="3527.y1003.60-44B-b12-1.239.O")[0],
    )
    Trips_Stops.objects.create(
        stop=Stop.objects.filter(id="8250DB002831")[0],
        trip=Trip.objects.filter(id="3527.y1003.60-44B-b12-1.239.O")[0],
    )


class ApiTests(TestCase):
    def setUp(self):
        setupTestData()

    def test_get_bus_stops(self):
        # compare the response from api and db, when inserting the same value

        # insert 44
        api_response_for_route44 = json.loads(
            self.client.get("/api/get_bus_stops/", {"route_number": "44"}).content
        )
        db_response_for_route44 = Trip.objects.filter(
            route=Route.objects.filter(short_name="44")[0]
        )
        for data in db_response_for_route44:
            self.assertTrue(data.headsign in api_response_for_route44)

        # insert 4b
        api_response_for_route44b = json.loads(
            self.client.get("/api/get_bus_stops/", {"route_number": "44b"}).content
        )
        db_response_for_route44b = Trip.objects.filter(
            route=Route.objects.filter(short_name="44b")[0]
        )
        for data in db_response_for_route44b:
            self.assertTrue(data.headsign in api_response_for_route44b)

        # insert a route that does not exist (route 88)
        api_response_for_route88 = json.loads(
            self.client.get("/api/get_bus_stops/", {"route_number": "88"}).content
        )
        self.assertEqual(len(api_response_for_route88), 0)

        # post request
        api_response_for_post = json.loads(
            self.client.post("/api/get_bus_stops/").content
        )
        self.assertTrue(api_response_for_post["error"] is not None)

    def test_weather_widget(self):
        # compare the response from api and cache
        api_response_timestamp = json.loads(
            self.client.get("/api/weather_widget").content
        )["_Weather__timestamp"]
        cache_data_timestamp = get_weather(
            datetime.now().timestamp() + 5
        ).get_timestamp()
        self.assertEqual(api_response_timestamp, cache_data_timestamp)

    def test_autocomple_route(self):
        # compare the response from api and db, when inserting the same value

        # insert 4
        api_response_when_insert_4 = json.loads(
            self.client.get("/api/autocomple_route", {"insert": "4"}).content
        )["data"]
        db_response_when_insert_4 = (
            Route.objects.filter(short_name__icontains="4")
            .values("short_name")
            .distinct()
        )
        self.assertEqual(
            len(api_response_when_insert_4), len(db_response_when_insert_4)
        )

        # insert 4b
        api_response_when_insert_4b = json.loads(
            self.client.get("/api/autocomple_route", {"insert": "4b"}).content
        )["data"]
        db_response_when_insert_4b = (
            Route.objects.filter(short_name__icontains="4b")
            .values("short_name")
            .distinct()
        )
        self.assertEqual(
            len(api_response_when_insert_4b), len(db_response_when_insert_4b)
        )

        # insert a route that does not exist (route 88)
        api_response_when_insert_88 = json.loads(
            self.client.get("/api/autocomple_route", {"insert": "88"}).content
        )["data"]
        db_response_when_insert_88 = (
            Route.objects.filter(short_name__icontains="88")
            .values("short_name")
            .distinct()
        )
        self.assertEqual(
            len(db_response_when_insert_88), len(api_response_when_insert_88)
        )

    def test_get_journey_travel_time_estimation_post_request_without_data(self):
        client = Client()
        api_response = client.post("/api/get_journey_travel_time_estimation/")
        response_json = api_response.json()
        self.assertEqual(
            response_json, {"error": "request.body cannot be parsed as a JSON object"}
        )

    def test_get_journey_travel_time_estimation_get_request(self):
        client = Client()
        api_response = client.get("/api/get_journey_travel_time_estimation/")
        response_json = api_response.json()
        self.assertEqual(
            response_json, {"error": "endpoint only accepts POST requests"}
        )

    def test_get_journey_travel_time_estimation_incorrect_keys(self):
        client = Client()
        api_response = client.post(
            "/api/get_journey_travel_time_estimation/",
            {"departure": "2021-08-12T12:53", "routes": []},
            content_type="application/json",
        )
        response_json = api_response.json()
        self.assertEqual(
            response_json,
            {"error": "JSON object must have 'routesData' and 'departureTime'"},
        )

    def test_get_journey_travel_time_estimation_with_correct_example_data(self):
        routes_data_example_correct = {
            "departureTime": "2021-08-12T13:00",
            "routesData": [
                [
                    {
                        "start_time": "Thu Aug 12 2021 13:03:44 GMT+0100 (Irish Standard Time)"
                    },
                    {"step": {"step_duration": 224, "travel_mode": "WALKING"}},
                    {
                        "step": {
                            "step_duration": 568,
                            "travel_mode": "TRANSIT",
                            "provider": "Dublin Bus",
                            "bus_line_long_name": "Mountjoy Square Park - Bride's Glen Bus Stop",
                            "bus_line_short_name": "7",
                            "headsign": "Mountjoy Square",
                            "departure_stop": "Clarence Place, stop 7825",
                            "arrival_stop": "Frascati SC, stop 3084",
                            "departure_time": "Thu Aug 12 2021 13:07:28 GMT+0100 (Irish Standard Time)",
                            "number_of_stops": 8,
                        }
                    },
                    {"step": {"step_duration": 392, "travel_mode": "WALKING"}},
                ],
                [
                    {
                        "start_time": "Thu Aug 12 2021 13:18:44 GMT+0100 (Irish Standard Time)"
                    },
                    {"step": {"step_duration": 197, "travel_mode": "WALKING"}},
                    {
                        "step": {
                            "step_duration": 887,
                            "travel_mode": "TRANSIT",
                            "provider": "Dublin Bus",
                            "bus_line_long_name": "Mountjoy Square Park - Loughlinstown Wood Estate",
                            "bus_line_short_name": "7A",
                            "headsign": "Mountjoy Square",
                            "departure_stop": "Dun Laoghaire SC, stop 3070",
                            "arrival_stop": "Patrick's Row, stop 3081",
                            "departure_time": "Thu Aug 12 2021 13:22:01 GMT+0100 (Irish Standard Time)",
                            "number_of_stops": 12,
                        }
                    },
                    {"step": {"step_duration": 250, "travel_mode": "WALKING"}},
                ],
                [
                    {
                        "start_time": "Thu Aug 12 2021 13:04:31 GMT+0100 (Irish Standard Time)"
                    },
                    {"step": {"step_duration": 749, "travel_mode": "WALKING"}},
                    {
                        "step": {
                            "step_duration": 240,
                            "travel_mode": "TRANSIT",
                            "provider": "Irish Rail",
                            "departure_time": "Thu Aug 12 2021 13:17:00 GMT+0100 (Irish Standard Time)",
                        }
                    },
                ],
                [
                    {
                        "start_time": "Thu Aug 12 2021 13:33:44 GMT+0100 (Irish Standard Time)"
                    },
                    {"step": {"step_duration": 224, "travel_mode": "WALKING"}},
                    {
                        "step": {
                            "step_duration": 568,
                            "travel_mode": "TRANSIT",
                            "provider": "Dublin Bus",
                            "bus_line_long_name": "Mountjoy Square Park - Bride's Glen Bus Stop",
                            "bus_line_short_name": "7",
                            "headsign": "Mountjoy Square",
                            "departure_stop": "Clarence Place, stop 7825",
                            "arrival_stop": "Frascati SC, stop 3084",
                            "departure_time": "Thu Aug 12 2021 13:37:28 GMT+0100 (Irish Standard Time)",
                            "number_of_stops": 8,
                        }
                    },
                    {"step": {"step_duration": 392, "travel_mode": "WALKING"}},
                ],
            ],
        }
        client = Client()
        api_response = client.post(
            "/api/get_journey_travel_time_estimation/",
            routes_data_example_correct,
            content_type="application/json",
        )
        response_json = api_response.json()
        # assert api returns a dictionary
        self.assertIs(type(response_json), dict)
        # assert api response returns information for the same number of routes sent to backend
        self.assertEqual(
            len(response_json), len(routes_data_example_correct["routesData"])
        )
        # assert response dict has the expected keys for first route
        self.assertIn("route_0", response_json)
        self.assertIn("journey_starts", response_json["route_0"])
        self.assertIn("journey_ends", response_json["route_0"])
        self.assertIn("route_duration", response_json["route_0"])
        # assert route has time estimations for all steps (3) of the first route
        self.assertIn("step_0", response_json["route_0"])
        self.assertIn("step_1", response_json["route_0"])
        self.assertIn("step_2", response_json["route_0"])

    def test_get_travel_time_for_route_correct_data(self):
        route_data_example = [
            {"start_time": "Thu Aug 12 2021 13:03:44 GMT+0100 (Irish Standard Time)"},
            {"step": {"step_duration": 224, "travel_mode": "WALKING"}},
            {
                "step": {
                    "step_duration": 568,
                    "travel_mode": "TRANSIT",
                    "provider": "Dublin Bus",
                    "bus_line_long_name": "Mountjoy Square Park - Bride's Glen Bus Stop",
                    "bus_line_short_name": "7",
                    "headsign": "Mountjoy Square",
                    "departure_stop": "Clarence Place, stop 7825",
                    "arrival_stop": "Frascati SC, stop 3084",
                    "departure_time": "Thu Aug 12 2021 13:07:28 GMT+0100 (Irish Standard Time)",
                    "number_of_stops": 8,
                }
            },
            {"step": {"step_duration": 392, "travel_mode": "WALKING"}},
        ]
        datetime_object = datetime.strptime("2021-08-12T13:00", "%Y-%m-%dT%H:%M")
        response = _get_travel_time_for_route(route_data_example, datetime_object)
        self.assertIs(type(response), dict)
        self.assertIn("journey_starts", response)
        self.assertIn("journey_ends", response)
        self.assertIn("route_duration", response)
        # route index keys are added by get_journey_travel_time_estimation not this function
        self.assertNotIn("route_0", response)
        # assert dict has time estimations for all steps (3) of the route_data_example
        self.assertIn("step_0", response)
        self.assertIn("step_1", response)
        self.assertIn("step_2", response)
        # assert first step has all the expected keys
        self.assertIn("step_starts", response["step_0"])
        self.assertIn("step_ends", response["step_0"])
        self.assertIn("number_of_stops", response["step_0"])
        self.assertIn("step_duration", response["step_0"])
        self.assertIn("step_cost", response["step_0"])

    def test_get_step_time_estimation_step_walking(self):
        step_data_example = {"step": {"step_duration": 224, "travel_mode": "WALKING"}}
        datetime_object = datetime.strptime("2021-08-12T13:00", "%Y-%m-%dT%H:%M")
        elapsed_time = datetime.strptime(
            "Thu Aug 12 2021 13:03:44 GMT+0100", f"%a %b %d %Y %H:%M:%S %Z%z"
        )
        (
            step_time_estimation,
            step_number_of_stops,
            step_starts,
            step_ends,
            step_duration,
            step_estimated_cost,
            route_name,
            predicted_by_app,
        ) = _get_step_time_estimation(step_data_example, datetime_object, elapsed_time)
        # assert returned values are as expected for this step
        self.assertEqual(
            step_time_estimation, step_data_example["step"]["step_duration"]
        )
        self.assertEqual(step_number_of_stops, 0)
        self.assertEqual(
            step_duration,
            _convert_number_of_seconds_to_time_string(step_time_estimation),
        )
        self.assertEqual(step_starts, _datetime_to_hour_minutes_string(elapsed_time))
        self.assertEqual(
            step_ends,
            _datetime_to_hour_minutes_string(
                elapsed_time + timedelta(seconds=step_time_estimation)
            ),
        )
        self.assertEqual(step_estimated_cost, "")
        self.assertEqual(route_name, "")
        self.assertEqual(predicted_by_app, False)

    def test_get_step_time_estimation_step_not_dublin_bus(self):
        step_data_example = {
            "step": {
                "step_duration": 960,
                "travel_mode": "TRANSIT",
                "provider": "Go-Ahead",
                "departure_time": "Thu Aug 12 2021 18:08:00 GMT+0100 (Irish Standard Time)",
            }
        }
        datetime_object = datetime.strptime("2021-08-12T17:10", "%Y-%m-%dT%H:%M")
        elapsed_time = datetime.strptime(
            "Thu Aug 12 2021 18:08:00 GMT+0100", f"%a %b %d %Y %H:%M:%S %Z%z"
        )
        (
            step_time_estimation,
            step_number_of_stops,
            step_starts,
            step_ends,
            step_duration,
            step_estimated_cost,
            route_name,
            predicted_by_app,
        ) = _get_step_time_estimation(step_data_example, datetime_object, elapsed_time)
        # assert returned values are as expected for this step
        self.assertEqual(
            step_time_estimation, step_data_example["step"]["step_duration"]
        )
        self.assertEqual(step_number_of_stops, 0)
        self.assertEqual(
            step_duration,
            _convert_number_of_seconds_to_time_string(step_time_estimation),
        )
        self.assertEqual(step_starts, _datetime_to_hour_minutes_string(elapsed_time))
        self.assertEqual(
            step_ends,
            _datetime_to_hour_minutes_string(
                elapsed_time + timedelta(seconds=step_time_estimation)
            ),
        )
        self.assertEqual(step_estimated_cost, "")
        self.assertEqual(route_name, "")
        self.assertEqual(predicted_by_app, False)

    def test_get_step_time_estimation_step_dublin_bus_not_in_db(self):
        dublin_bus_step_not_exists_in_db = {
            "step": {
                "step_duration": 921,
                "travel_mode": "TRANSIT",
                "provider": "Dublin Bus",
                "bus_line_long_name": "Phoenix Park Gate - University College Dublin",
                "bus_line_short_name": "46A",
                "headsign": "Dun Laoghaire",
                "departure_stop": "Stephen's Green East",
                "arrival_stop": "Booterstown, Woodbine Road",
                "departure_time": "Thu Aug 12 2021 17:56:17 GMT+0100 (Irish Standard Time)",
                "number_of_stops": 14,
            }
        }
        datetime_object = datetime.strptime("2021-08-12T17:50", "%Y-%m-%dT%H:%M")
        elapsed_time = datetime.strptime(
            "Thu Aug 12 2021 17:51:00 GMT+0100", f"%a %b %d %Y %H:%M:%S %Z%z"
        )
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
            dublin_bus_step_not_exists_in_db, datetime_object, elapsed_time
        )
        # assert returned values are as expected for this step that will not be predicted by the app since we don't have all bus stops in the database
        self.assertEqual(
            step_time_estimation,
            dublin_bus_step_not_exists_in_db["step"]["step_duration"],
        )
        self.assertEqual(step_number_of_stops, 14)
        self.assertEqual(
            step_duration,
            _convert_number_of_seconds_to_time_string(step_time_estimation),
        )
        self.assertEqual(step_starts, _datetime_to_hour_minutes_string(elapsed_time))
        self.assertEqual(
            step_ends,
            _datetime_to_hour_minutes_string(
                elapsed_time + timedelta(seconds=step_time_estimation)
            ),
        )
        self.assertEqual(step_estimated_cost, "€2.50")
        self.assertEqual(route_name, "46A")
        self.assertEqual(predicted_by_app, False)

    def test_datetime_to_hour_minutes_string_until_10_mins(self):
        datetime_object = datetime.strptime(
            "Thu Aug 12 2021 18:08:00 GMT+0100", f"%a %b %d %Y %H:%M:%S %Z%z"
        )
        time_string = _datetime_to_hour_minutes_string(datetime_object)
        self.assertEqual(time_string, "18:08")

    def test_datetime_to_hour_minutes_string_after_10_mins(self):
        datetime_object = datetime.strptime(
            "Thu Aug 12 2021 15:18:00 GMT+0100", f"%a %b %d %Y %H:%M:%S %Z%z"
        )
        time_string = _datetime_to_hour_minutes_string(datetime_object)
        self.assertEqual(time_string, "15:18")

    def test_datetime_to_hour_minutes_string_before_12pm(self):
        datetime_object = datetime.strptime(
            "Thu Aug 12 2021 05:18:00 GMT+0100", f"%a %b %d %Y %H:%M:%S %Z%z"
        )
        time_string = _datetime_to_hour_minutes_string(datetime_object)
        self.assertEqual(time_string, "5:18")

    def test_convert_number_of_seconds_to_time_string_before_2_hours(self):
        seconds = 4200
        time_string = _convert_number_of_seconds_to_time_string(seconds)
        self.assertEqual(time_string, "1 hour 10 mins")

    def test_convert_number_of_seconds_to_time_string_after_2_hours(self):
        seconds = 7400
        time_string = _convert_number_of_seconds_to_time_string(seconds)
        self.assertEqual(time_string, "2 hours 3 mins")

    def test_calculate_step_cost(self):
        for i in range(1, 20):
            cost = _calculate_step_cost(i)
            if i <= 3:
                self.assertEqual(cost, "€1.55")
            elif i <= 13:
                self.assertEqual(cost, "€2.25")
            else:
                self.assertEqual(cost, "€2.50")

    def test_gtfsr_response(self):

        # test cache initialisation
        api_response = json.loads(self.client.get("/api/get_gtfsr_response/").content)
        cache_response = get_last_gtfsr_response()
        self.assertEqual(api_response, cache_response)

        # test cache after initialisation
        api_response = json.loads(self.client.get("/api/get_gtfsr_response/").content)
        self.assertEqual(api_response, cache_response)

    def test_get_bus_stop_times(self):
        # when stop_id is not set
        response_no_stop_id = json.loads(
            self.client.get("/api/get_bus_stop_times/").content
        )
        self.assertTrue(response_no_stop_id["error"] is not None)

        # normal case
        response_normal = json.loads(
            self.client.get(
                "/api/get_bus_stop_times/", {"stop_id": "8220DB000044"}
            ).content
        )

        now = datetime.now()
        hour_ahead = now + timedelta(hours=1)
        current_time = now.strftime("%H:%M:%S")
        current_time_1hr = hour_ahead.strftime("%H:%M:%S")

        stop_times = Stop_Times.objects.filter(
            stop_id="8220DB000044",
            arrival_time__gte=current_time,
            arrival_time__lte=current_time_1hr,
        )
        # there are 3 types of service days, today must be seen as one type, so divide it by 3
        self.assertEqual(len(stop_times) / 3, len(response_normal))

    def test_get_all_bus_stops(self):
        # stop_name is not set
        response_no_stop_name = json.loads(
            self.client.get("/api/get_all_bus_stops/").content
        )
        self.assertTrue(len(response_no_stop_name) > 0)

        # stop_name is set
        response_with_stop_name = json.loads(
            self.client.get(
                "/api/get_all_bus_stops/", {"stop_name": "Dun Emer Road, stop 2830"}
            ).content
        )
        self.assertEqual(len(response_with_stop_name), 1)

    def test_autocomple_stop(self):
        response_normal = json.loads(
            self.client.get("/api/autocomple_stop", {"insert": "Dun Emer"}).content
        )["data"]
        self.assertEqual(len(response_normal), 1)

    def test_model_prediction(self):
        weather_types = ["Clouds", "Drizzle", "Fog", "Mist", "Rain", "Smoke", "Snow"]
        for weather in weather_types:
            prediction = main.api.model_prediction(123, 3, 1, 1, 6, 12, weather, 13)
            self.assertTrue(prediction > 0 or prediction == 0)

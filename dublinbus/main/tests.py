from django.urls import reverse
from django.test import TestCase
from main.cache_manipulator import get_weather
from datetime import datetime
import pytz
from main.models import Route, Trip, Trips_Stops, Stop
import json


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

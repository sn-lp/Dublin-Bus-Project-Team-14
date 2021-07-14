from django.urls import reverse
from django.test import TestCase
from main.cache_manipulator import get_weather
from datetime import datetime
import pytz


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
        self.assertEqual(get_weather(before_1min_timestamp), None)

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

from apscheduler.schedulers.background import BackgroundScheduler
from django.core.cache import cache
from main import weather_kits
from datetime import datetime
import pytz
from django.http import JsonResponse


def update_weather_data():
    hourly_weather_dic, daily_weather_dic = weather_kits.scrape()
    # hourly_weather_dic is a list (index: hours from now, value: weather object)
    # daily_weather_dic is a list (index: days from now,  value: weather object)
    # expire time: 65 minutes
    cache.set("hourly_weather_dic", hourly_weather_dic, 65 * 60)
    cache.set("daily_weather_dic", daily_weather_dic, 65 * 60)
    print("RUN WEATHER UPDATE")  # this could be changed, when we have a logging module


def update_weather_data_hourly():
    scheduler = BackgroundScheduler()
    # use cron to run hourly
    scheduler.add_job(update_weather_data, "cron", minute=0)
    scheduler.start()


def get_weather(input_timestamp):
    current_timestamp = datetime.now().timestamp()
    # if input is before current time
    if input_timestamp < current_timestamp:
        input_timestamp = current_timestamp

    # set timezone
    current_datetime = datetime.fromtimestamp(
        current_timestamp, tz=pytz.timezone("Europe/Dublin")
    )
    input_datetime = datetime.fromtimestamp(
        input_timestamp, tz=pytz.timezone("Europe/Dublin")
    )
    # truncate time
    truncated_current_datetime = current_datetime.replace(
        minute=0, second=0, microsecond=0
    )
    truncated_input_datetime = input_datetime.replace(minute=0, second=0, microsecond=0)
    truncated_current_timestamp = truncated_current_datetime.timestamp()
    truncated_input_timestamp = truncated_input_datetime.timestamp()

    # if input is 7 days after

    input_day = truncated_input_datetime.replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    current_day = truncated_current_datetime.replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    if (input_day - current_day).days > 7:
        return None

    # if cache has no data, then scrape the data and put it in cache
    if (
        cache.get("hourly_weather_dic") is None
        or cache.get("daily_weather_dic") is None
    ):
        # this could be changed, when we have a logging module
        print("Error: No value in Cache")
        update_weather_data()

    # after trying one time, still has no data, then return None
    if (
        cache.get("hourly_weather_dic") is None
        or cache.get("daily_weather_dic") is None
    ):
        # this could be changed, when we have a logging module
        print("Error: cannot load weather api data")
        return None

    # if the input is within 48 hour (169200 sec), then retrieve the hourly data
    if truncated_input_timestamp - truncated_current_timestamp <= 169200:
        hour_index = int(
            (truncated_input_timestamp - truncated_current_timestamp) / 3600
        )
        return cache.get("hourly_weather_dic")[hour_index]

    # if input is between 48 hr and 7 days, then use the daily data
    else:
        daily_index = int(
            (truncated_input_timestamp - truncated_current_timestamp) / (24 * 3600)
        )
        return cache.get("daily_weather_dic")[daily_index]


def update_gtfsr_response(gtfsr_response):
    cache.set("gtfsr", gtfsr_response, 60)  # will be kept in cache for 60 seconds


def get_last_gtfsr_response():
    return cache.get("gtfsr")

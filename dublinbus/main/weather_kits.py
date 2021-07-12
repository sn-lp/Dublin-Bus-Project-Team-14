import requests
import datetime
import os
from django.conf import settings


class Weather:
    def __init__(
        self,
        timestamp,
        temp,
        feels_like,
        pressure,
        humidity,
        wind_speed,
        wind_deg,
        weather_id,
        weather_main,
        weather_icon,
        weather_description,
    ):

        self.__timestamp = timestamp
        self.__temp = temp
        self.__feels_like = feels_like
        self.__pressure = pressure
        self.__humidity = humidity
        self.__wind_speed = wind_speed
        self.__wind_deg = wind_deg
        self.__weather_id = weather_id
        self.__weather_main = weather_main
        self.__weather_icon = weather_icon
        self.__weather_description = weather_description

    def get_timestamp(self):
        return self.__timestamp

    def get_temp(self):
        return self.__temp

    def get_feels_like(self):
        return self.__feels_like

    def get_pressure(self):
        return self.__pressure

    def get_humidity(self):
        return self.__humidity

    def get_wind_speed(self):
        return self.__wind_speed

    def get_wind_deg(self):
        return self.__wind_deg

    def get_weather_id(self):
        return self.__weather_id

    def get_weather_main(self):
        return self.__weather_main

    def get_weather_icon(self):
        return self.__weather_icon

    def get_weather_description(self):
        return self.__weather_description


def parse(object, is_daily):
    timestamp = object["dt"]
    if is_daily:
        temp = object["temp"]
        feels_like = object["feels_like"]
    else:
        temp = (object["temp"]["max"] + object["temp"]["min"]) / 2
        feels_like = (object["feels_like"]["day"] + object["feels_like"]["night"]) / 2
    pressure = object["pressure"]
    humidity = object["humidity"]
    wind_speed = object["wind_speed"]
    wind_deg = object["wind_deg"]
    weather_id = object["weather"][0]["id"]
    weather_main = object["weather"][0]["main"]
    weather_description = object["weather"][0]["description"]
    weather_icon = object["weather"][0]["icon"]

    return Weather(
        timestamp,
        temp,
        feels_like,
        pressure,
        humidity,
        wind_speed,
        wind_deg,
        weather_id,
        weather_main,
        weather_icon,
        weather_description,
    )


def scrape():
    if settings.WEATHER_APIKEY is None:
        print("ERROR: no WEATHER_APIKEY set!")
        return None, None
    url = (
        "http://api.openweathermap.org/data/2.5/onecall?lat=53.349805&lon=-6.26031&units=metric&appid="
        + "27ca9208d8aa854c6556a76e6521c4dc"
    )

    response = requests.get(url)
    response.raise_for_status()

    if response:
        data = response.json()

        # index: hours from now, value: weather object
        hourly_weather_dic = []
        for hourly_data in data["hourly"]:
            weather = parse(hourly_data, True)
            hourly_weather_dic.append(weather)

        # index: days from now, value: weather object
        daily_weather_dic = []
        for daily_data in data["daily"]:
            weather = parse(daily_data, False)
            daily_weather_dic.append(weather)

    return hourly_weather_dic, daily_weather_dic

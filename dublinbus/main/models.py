from django.db import models


class Route(models.Model):
    id = models.CharField(primary_key=True, max_length=30)
    short_name = models.CharField(max_length=10)

    class Meta:
        db_table = "routes"


# a trip belongs to one route and one route can have many trips
# this table captures this one-to-many relationship
class Trip(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    headsign = models.CharField(max_length=200)
    direction = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "trips"


class Stop(models.Model):
    id = models.CharField(primary_key=True, max_length=30)
    name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        db_table = "stops"


# one trip can have many stops and one stop can belong to many trips
# this table captures this many-to-many relationship
class Trips_Stops(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    stop = models.ForeignKey(Stop, on_delete=models.CASCADE)
    progress_number = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "trips_stops"


class Stop_Times(models.Model):
    # id = models.CharField(primary_key=True, max_length=30)
    trip_id = models.CharField(max_length=50)
    arrival_time = models.TimeField()
    stop_id = models.CharField(max_length=50)
    id = models.IntegerField(primary_key=True)

    class Meta:
        db_table = "stop_times"

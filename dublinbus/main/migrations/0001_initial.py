# Generated by Django 3.2.4 on 2021-07-05 15:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Route",
            fields=[
                (
                    "id",
                    models.CharField(max_length=30, primary_key=True, serialize=False),
                ),
                ("short_name", models.CharField(max_length=10)),
            ],
            options={
                "db_table": "routes",
            },
        ),
        migrations.CreateModel(
            name="Stop",
            fields=[
                (
                    "id",
                    models.CharField(max_length=30, primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=200)),
                ("latitude", models.FloatField()),
                ("longitude", models.FloatField()),
            ],
            options={
                "db_table": "stops",
            },
        ),
        migrations.CreateModel(
            name="Trip",
            fields=[
                (
                    "id",
                    models.CharField(max_length=50, primary_key=True, serialize=False),
                ),
                ("headsign", models.CharField(max_length=200)),
                (
                    "route",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="main.route"
                    ),
                ),
            ],
            options={
                "db_table": "trips",
            },
        ),
        migrations.CreateModel(
            name="Trips_Stops",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "stop_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="main.stop"
                    ),
                ),
                (
                    "trip_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="main.trip"
                    ),
                ),
            ],
            options={
                "db_table": "trips_stops",
            },
        ),
    ]
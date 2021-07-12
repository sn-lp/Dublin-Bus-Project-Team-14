from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "main"

    def ready(self):
        from main import cache_manipulator

        cache_manipulator.update_weather_cache_hourly()

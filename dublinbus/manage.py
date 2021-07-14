#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from main import cache_manipulator
from django.core.cache import cache


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dublinbus.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # run the weather scraper and put the data in cache right after the server started
    cache.clear()
    cache_manipulator.update_weather_data()
    execute_from_command_line(sys.argv)
    cache.clear()


if __name__ == "__main__":
    main()

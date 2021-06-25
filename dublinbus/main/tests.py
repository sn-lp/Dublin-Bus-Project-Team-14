from django.conf import settings
from django.urls import reverse
from django.test import TestCase


class ViewTests(TestCase):
    def test_index_view(self):
        with settings.GOOGLE_MAPS_API_KEY:
            response = self.client.get(reverse("home"))
            self.assertEqual(response.status_code, 200)

    def test_real_time_view(self):
        response = self.client.get(reverse("realtime"))
        self.assertEqual(response.status_code, 200)

    def test_routes_view(self):
        response = self.client.get(reverse("busroutes"))
        self.assertEqual(response.status_code, 200)

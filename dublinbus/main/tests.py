from django.urls import reverse
from django.test import TestCase


class ViewTests(TestCase):
    def test_index_view(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

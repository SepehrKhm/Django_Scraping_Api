from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import ScrapeTask

class ScrapeTaskTests(APITestCase):
    def test_create_scrape_task(self):
        url = reverse('scrape-create')
        data = {
            'url': 'https://example.com',
            'selector': 'h1'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ScrapeTask.objects.count(), 1)
        self.assertEqual(ScrapeTask.objects.get().url, 'https://example.com')

    def test_invalid_url(self):
        url = reverse('scrape-create')
        data = {
            'url': 'not-a-url',
            'selector': 'h1'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

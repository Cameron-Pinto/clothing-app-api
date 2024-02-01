"""
Test for the garments API
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient

from core.models import Garment

from collection.serializers import GarmentSerializer


GARMENTS_URL = reverse("collection:garment-list")


def detail_url(garment_id):
    """Create and return garment detail URL"""
    return reverse('collection:garment-detail', args=[garment_id])


def create_user(email="user@example.com", password="test123"):
    """Create and return user"""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicGarmentAPITests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving ingredients"""
        res = self.client.get(GARMENTS_URL)

        self.assertEqual(res.status_code, 401)


class PrivateGarmentAPITest(TestCase):
    """Test authetnticated API request"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retreive_garments(self):
        """Test retriving a list of garments"""
        Garment.objects.create(user=self.user, name="Sweater")
        Garment.objects.create(user=self.user, name="Shirt")

        res = self.client.get(GARMENTS_URL)

        garments = Garment.objects.all().order_by("-name")
        serializer = GarmentSerializer(garments, many=True)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, serializer.data)

    def test_garment_limited_to_user(self):
        """Test list of garments is limited to authenticate user"""
        user2 = create_user(email="user2@example.com")
        Garment.objects.create(user=user2, name="Pants")
        garment = Garment.objects.create(user=self.user, name="Socks")

        res = self.client.get(GARMENTS_URL)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], garment.name)
        self.assertEqual(res.data[0]['id'], garment.id)

    def test_update_garment(self):
        """Test updating a garment"""
        garment = Garment.objects.create(user=self.user, name='Undershirt')

        payload = {'name': 'T-shirt'}
        url = detail_url(garment.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, 200)
        garment.refresh_from_db()
        self.assertEqual(garment.name, payload['name'])

    def test_delete_garment(self):
        """Test the deletion of a garment"""
        garment = Garment.objects.create(user=self.user, name='Shorts')

        url = detail_url(garment.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, 204)
        garments = Garment.objects.filter(user=self.user)
        self.assertFalse(garments.exists())

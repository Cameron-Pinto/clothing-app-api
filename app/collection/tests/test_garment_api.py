"""
Test for the garments API
"""
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient

from core.models import (
    Garment,
    Collection,
)

from collection.serializers import GarmentSerializer


GARMENTS_URL = reverse("collection:garment-list")


def detail_url(garment_id):
    """Create and return garment detail URL"""
    return reverse('collection:garment-detail', args=[garment_id])


def image_upload_url(collection_id):
    """Create and reutrn an image uplodd URL"""
    return reverse("collection:garment-upload-image", args=[collection_id])


def create_garment(user, **params):
    """Create and return sample garment"""
    defaults = {
        "name": "Sample garment name",
    }
    defaults.update(params)

    garment = Garment.objects.create(user=user, **defaults)
    return garment


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


class ImageUploadTests(TestCase):
    """Test for image upload API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@example.com",
            "password123",
        )
        self.client.force_authenticate(self.user)
        self.garment = create_garment(user=self.user)

    def test_upload(self):
        """Test uploading and image to garment"""
        url = image_upload_url(self.garment.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            payload = {"image": image_file}
            res = self.client.post(url, payload, format="multipart")

        self.garment.refresh_from_db()
        self.assertEqual(res.status_code, 200)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.garment.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image"""
        url = image_upload_url(self.garment.id)
        payload = {"image": "not an image"}
        res = self.client.post(url, payload, format="multipart")

        self.assertEqual(res.status_code, 400)

    def tearDown(self):
        self.garment.image.delete()

    def test_filter_garments_in_collections(self):
        """Test listing garments in collections"""
        gar1 = Garment.objects.create(user=self.user, name='Shirt')
        gar2 = Garment.objects.create(user=self.user, name='Sweater')
        collection = Collection.objects.create(
            title='Tops',
            user=self.user,
        )
        collection.garments.add(gar1)

        res = self.client.get(GARMENTS_URL, {'assigned_only': 1})

        s1 = GarmentSerializer(gar1)
        s2 = GarmentSerializer(gar2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_garments_unique(self):
        """Test filtered garments returns a unique list"""
        gar = Garment.objects.create(user=self.user, name='Shirt')
        Garment.objects.create(user=self.user, name='Sweater')
        collection1 = Collection.objects.create(
            title='Closet',
            user=self.user,
        )
        collection2 = Collection.objects.create(
            title='Drawer',
            user=self.user,
        )
        collection1.garments.add(gar)
        collection2.garments.add(gar)

        res = self.client.get(GARMENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)

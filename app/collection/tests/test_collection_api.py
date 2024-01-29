"""
Test for collection API
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Collection

from collection.serializers import (
    CollectionSerializer,
    CollectionDetailSerializer,
)


COLLECTION_URL = reverse("collection:collection-list")


def detail_url(collection_id):
    """Create and return collection details URL"""
    return reverse("collection:collection-detail", args=[collection_id])


def create_collection(user, **params):
    """Create and return sample collection"""
    defaults = {
        "title": "Sample collection title",
        "description": "Sample description",
        "link": "http://example.com/collection.pdf",
    }
    defaults.update(params)

    collection = Collection.objects.create(user=user, **defaults)
    return collection


def create_user(**params):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**params)


class PublicCollectionAPITests(TestCase):
    """Test unauthenticated API request"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test authentication required for API call"""
        res = self.client.get(COLLECTION_URL)

        self.assertEqual(res.status_code, 200)


class PrivateCollectionAPITests(TestCase):
    """Tests authenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="user@example.com", password="test123")
        self.client.force_authenticate(self.user)

    def test_retrieve_collection(self):
        """Test receiveing a list of collections"""
        create_collection(user=self.user)
        create_collection(user=self.user)

        res = self.client.get(COLLECTION_URL)

        collection = Collection.objects.all().order_by("-id")
        serializer = CollectionSerializer(collection, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_collection_list_for_user(self):
        """Test collections limited to authenticated user"""
        other_user = create_user(email="other@example.com", password="test123")
        create_collection(user=other_user)
        create_collection(user=self.user)

        res = self.client.get(COLLECTION_URL)

        collection = Collection.objects.filter(user=self.user)
        serializer = CollectionSerializer(collection, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_collection_detail(self):
        """Test getting collection details"""
        collection = create_collection(user=self.user)

        url = detail_url(collection.id)
        res = self.client.get(url)

        serializer = CollectionDetailSerializer(collection)
        self.assertEqual(res.data, serializer.data)

    def test_create_collection(self):
        """Test creating a collection through API"""
        payload = {
            "title": "Sample Collection",
            "description": "Sample Description",
        }
        res = self.client.post(COLLECTION_URL, payload)

        self.assertEqual(res.status_code, 201)
        collection = Collection.objects.get(id=res.data["id"])
        for key, value in payload.items():
            self.assertEqual(getattr(collection, key), value)
        self.assertEqual(collection.user, self.user)

    def test_partial_update(self):
        """Test partial update of a collection"""
        original_link = "https://example.com/collection.pdf"
        collection = create_collection(
            user=self.user,
            title="Sample Title",
            link=original_link,
        )

        payload = {"title": "New recipe title"}
        url = detail_url(collection.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, 200)
        collection.refresh_from_db()
        self.assertEqual(collection.title, payload["title"])
        self.assertEqual(collection.link, original_link)
        self.assertEqual(collection.user, self.user)

    def test_full_update(self):
        """Test full update of a collection"""
        collection = create_collection(
            user=self.user,
            title="Sample collection",
            link="https://example.com/collection.pdf",
            description="Sample description",
        )

        payload = {
            "title": "New title",
            "link": "https://example.com/new-collection.pdf",
            "description": "New description",
        }
        url = detail_url(collection.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, 200)
        collection.refresh_from_db()
        for key, value in payload.items():
            self.assertEqual(getattr(collection, key), value)
        self.assertEqual(collection.user, self.user)

    def test_update_user_returns_update(self):
        """Test changing the collection user displays error"""
        new_user = create_user(email="other@example.com", password="test123")
        collection = create_collection(user=self.user)

        payload = {"user": new_user.id}
        url = detail_url(collection.id)
        self.client.patch(url, payload)

        collection.refresh_from_db()
        self.assertEqual(collection.user, self.user)

    def test_delete_collection(self):
        """Test the deletion of a collection"""
        collection = create_collection(user=self.user)

        url = detail_url(collection.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, 204)
        self.assertFalse(Collection.objects.filter(id=collection.id).exists())

    def test_collection_other_delete_error(self):
        """Test trying to delete another users recipe dipalys error"""
        new_user = create_user(email="other@example.com", password="test123")
        collection = create_collection(user=new_user)

        url = detail_url(collection.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, 404)
        self.assertTrue(Collection.objects.filter(id=collection.id).exists())

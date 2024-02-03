"""
Tests for the tags API
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient

from core.models import (
    Tag,
    Collection,
)

from collection.serializers import TagSerializer


TAGS_URL = reverse("collection:tag-list")


def detail_url(tag_id):
    """Create and return tag url"""
    return reverse('collection:tag-detail', args=[tag_id])


def create_user(email="user@example.com", password="testpass123"):
    """Create and return user"""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsAPITests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, 401)


class PrivateTagsAPITests(TestCase):
    """Tests authenticated API requests"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving list of tags"""
        Tag.objects.create(user=self.user, name="Spring")
        Tag.objects.create(user=self.user, name="Summer")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test list of tags are limited to authenticated user"""
        user2 = create_user(email="user2@example.com")
        Tag.objects.create(user=user2, name="Warm")
        tag = Tag.objects.create(user=self.user, name="Comfy Clothes")

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_updated_tag(self):
        """Test updating a tag"""
        tag = Tag.objects.create(user=self.user, name='Sweater Weather')

        payload = {'name': 'Fall'}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, 200)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        """Test the deletion of tags"""
        tag = Tag.objects.create(user=self.user, name='Spring')

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, 204)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_filter_tags_in_collection(self):
        """Test listing tags assinged to collection"""
        tag1 = Tag.objects.create(user=self.user, name='Summer')
        tag2 = Tag.objects.create(user=self.user, name='Spring')
        collection = Collection.objects.create(
            title='Seasonal',
            user=self.user,
        )
        collection.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_tags_unique(self):
        """Test filtered tags returns a unique list"""
        tag = Tag.objects.create(user=self.user, name="Shirt")
        Tag.objects.create(user=self.user, name="Sweater")
        collection1 = Collection.objects.create(
            title="Closet",
            user=self.user,
        )
        collection2 = Collection.objects.create(
            title="Drawer",
            user=self.user,
        )
        collection1.tags.add(tag)
        collection2.tags.add(tag)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)

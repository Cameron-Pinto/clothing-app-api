"""
Test for collection API
"""
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Collection,
    Tag,
    Garment,
)

from collection.serializers import (
    CollectionSerializer,
    CollectionDetailSerializer,
)


COLLECTION_URL = reverse("collection:collection-list")


def detail_url(collection_id):
    """Create and return collection details URL"""
    return reverse("collection:collection-detail", args=[collection_id])


def image_upload_url(collection_id):
    """Create and reutrn an image uplodd URL"""
    return reverse('collection:collection-upload-image', args=[collection_id])


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

        self.assertEqual(res.status_code, 403)


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

    def test_create_collection_with_tag(self):
        """Test the creation of collection with tags"""
        payload = {
            "title": "Summer Collection",
            "description": "Shorts and T-shirts",
            "tags": [{"name": "Athletic"}, {"name": "Beachwear"}],
        }
        res = self.client.post(COLLECTION_URL, payload, format="json")

        self.assertEqual(res.status_code, 201)
        collections = Collection.objects.filter(user=self.user)
        self.assertEqual(collections.count(), 1)
        collection = collections[0]
        self.assertEqual(collection.tags.count(), 2)
        for tag in payload["tags"]:
            exists = collection.tags.filter(
                name=tag["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_collection_with_existing_tags(self):
        """Test creating a collection with existing tag"""
        tag_summer = Tag.objects.create(user=self.user, name="Summer")
        payload = {
            "title": "Swimsuit",
            "description": "Floral patterns",
            "tags": [{"name": "Summer"}, {"name": "Vacation"}],
        }
        res = self.client.post(COLLECTION_URL, payload, format="json")

        self.assertEqual(res.status_code, 201)
        collections = Collection.objects.filter(user=self.user)
        self.assertEqual(collections.count(), 1)
        collection = collections[0]
        self.assertEqual(collection.tags.count(), 2)
        self.assertIn(tag_summer, collection.tags.all())

    def test_create_tag_on_update(self):
        """Test creating a tag when updating a collection"""
        collection = create_collection(user=self.user)

        payload = {"tags": [{"name": "Summer"}]}
        url = detail_url(collection.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, 200)
        new_tag = Tag.objects.get(user=self.user, name="Summer")
        self.assertIn(new_tag, collection.tags.all())

    def test_update_collection_assign_tag(self):
        """Test assigning an existing tag when updating a collection"""
        tag_spring = Tag.objects.create(user=self.user, name="Spring")
        collection = create_collection(user=self.user)
        collection.tags.add(tag_spring)

        tag_summer = Tag.objects.create(user=self.user, name="Summer")
        payload = {"tags": [{"name": "Summer"}]}
        url = detail_url(collection.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, 200)
        self.assertIn(tag_summer, collection.tags.all())
        self.assertNotIn(tag_spring, collection.tags.all())

    def test_clear_collection_tags(self):
        """Test clearing a collections tags"""
        tag_spring = Tag.objects.create(user=self.user, name="Spring")
        collection = create_collection(user=self.user)
        collection.tags.add(tag_spring)

        payload = {"tags": []}
        url = detail_url(collection.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(collection.tags.count(), 0)

    def test_create_collection_with_garments(self):
        """Test creating a recipe with new garments"""
        payload = {
            "title": "Spring",
            "description": "Spring must-haves",
            "garments": [{"name": "rain jacket"}, {"name": "boots"}],
        }
        res = self.client.post(COLLECTION_URL, payload, format="json")

        self.assertEqual(res.status_code, 201)
        collections = Collection.objects.filter(user=self.user)
        self.assertEqual(collections.count(), 1)
        collection = collections[0]
        self.assertEqual(collection.garments.count(), 2)
        for garment in payload["garments"]:
            exists = collection.garments.filter(
                name=garment["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_collection_with_existing_garment(self):
        """Test creating a collection with existing garment"""
        garment = Garment.objects.create(user=self.user, name="Bikini")
        payload = {
            "title": "Swimsuit",
            "description": "Floral patterns",
            "garments": [{"name": "Bikini"}, {"name": "Sunhat"}],
        }
        res = self.client.post(COLLECTION_URL, payload, format="json")

        self.assertEqual(res.status_code, 201)
        collections = Collection.objects.filter(user=self.user)
        self.assertEqual(collections.count(), 1)
        collection = collections[0]
        self.assertEqual(collection.garments.count(), 2)
        self.assertIn(garment, collection.garments.all())
        for garment in payload["garments"]:
            exists = collection.garments.filter(
                name=garment["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_garment_on_update(self):
        """Test creating a garment when updating a collection"""
        collection = create_collection(user=self.user)

        payload = {"garments": [{"name": "Hat"}]}
        url = detail_url(collection.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, 200)
        new_garment = Garment.objects.get(user=self.user, name="Hat")
        self.assertIn(new_garment, collection.garments.all())

    def test_update_collection_assign_garment(self):
        """Test assigning an existing garment when updating a collection"""
        garment1 = Garment.objects.create(user=self.user, name="Shirt")
        collection = create_collection(user=self.user)
        collection.garments.add(garment1)

        garment2 = Garment.objects.create(user=self.user, name="Sweater")
        payload = {"garments": [{"name": "Sweater"}]}
        url = detail_url(collection.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, 200)
        self.assertIn(garment2, collection.garments.all())
        self.assertNotIn(garment1, collection.garments.all())

    def test_clear_collection_garments(self):
        """Test clearing a collections garments"""
        garment = Garment.objects.create(user=self.user, name="Sweater")
        collection = create_collection(user=self.user)
        collection.garments.add(garment)

        payload = {"garments": []}
        url = detail_url(collection.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(collection.garments.count(), 0)

    def test_filter_tags(self):
        """Test filtering collections by tags"""
        c1 = create_collection(user=self.user, title="Summer")
        c2 = create_collection(user=self.user, title='Spring')
        tag1 = Tag.objects.create(user=self.user, name='Beach')
        tag2 = Tag.objects.create(user=self.user, name='Rainy')
        c1.tags.add(tag1)
        c2.tags.add(tag2)
        c3 = create_collection(user=self.user, title='Fall')

        params = {'tags': f'{tag1.id}, {tag2.id}'}
        res = self.client.get(COLLECTION_URL, params)

        s1 = CollectionSerializer(c1)
        s2 = CollectionSerializer(c2)
        s3 = CollectionSerializer(c3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingredients(self):
        """Test filtering collections by garments"""
        c1 = create_collection(user=self.user, title="Summer")
        c2 = create_collection(user=self.user, title="Spring")
        gar1 = Garment.objects.create(user=self.user, name='T-shirt')
        gar2 = Garment.objects.create(user=self.user, name='Rain jacket')
        c1.garments.add(gar1)
        c2.garments.add(gar2)
        c3 = create_collection(user=self.user, title='Fall')

        params = {'garments': f'{gar1.id}, {gar2.id}'}
        res = self.client.get(COLLECTION_URL, params)

        s1 = CollectionSerializer(c1)
        s2 = CollectionSerializer(c2)
        s3 = CollectionSerializer(c3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTests(TestCase):
    """Test for image upload API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'password123',
        )
        self.client.force_authenticate(self.user)
        self.collection = create_collection(user=self.user)

    def test_upload(self):
        """Test uploading and image to collection"""
        url = image_upload_url(self.collection.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.collection.refresh_from_db()
        self.assertEqual(res.status_code, 200)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.collection.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image"""
        url = image_upload_url(self.collection.id)
        payload = {'image': 'not an image'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, 400)

    def tearDown(self):
        self.collection.image.delete()

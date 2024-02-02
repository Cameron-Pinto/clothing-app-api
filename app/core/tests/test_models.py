"""
Test for models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models

from unittest.mock import patch


def create_user(email='user@email.com', password='test123'):
    """Create and return new user"""
    return get_user_model().objects.create_user(email, password)


class ModelTest(TestCase):
    """Test model"""

    def test_create_user_email(self):
        """Testing that user has valid email address"""
        email = "test@example.com"
        password = "password123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_create_user_email_normalized(self):
        """Testing email address normalization for new users"""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email(self):
        """Test that ValueError is raised for blank email"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_superuser(self):
        """Testing the creation of a superuser"""
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test123'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_collection(self):
        """Test the successful creation of a collection"""
        user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass123',
        )
        collection = models.Collection.objects.create(
            user=user,
            title='Sample Collection',
            description='Sample description'
        )

        self.assertEqual(str(collection), collection.title)

    def test_tag_create(self):
        """Test to create a tag successfully"""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='Tag1')

        self.assertEqual(str(tag), tag.name)

    def test_create_garment(self):
        """Test creating a garment is successful"""
        user = create_user()
        garment = models.Garment.objects.create(
            user=user,
            name='Sweater1',
        )

        self.assertEqual(str(garment), garment.name)

    @patch('core.models.uuid.uuid4')
    def test_collection_file_name_uuid(self, mock_uuid):
        """Tests generating image path"""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.collection_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/collection/{uuid}.jpg')

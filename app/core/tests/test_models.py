"""
Test for models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


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

    def test_tag_creat(self):
        """Test to create a tag successfully"""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='Tag1')

        self.assertEqual(str(tag), tag.name)

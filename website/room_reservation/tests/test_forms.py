from django.test import TestCase, Client
from django.contrib.auth.models import User
from room_reservation.models import Room


class PeerReviewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='myself',
            password='123',
        )

        cls.room = Room.objects.create(
            name="New York",
            location="Merc 0.1337",
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username='myself', password='123')

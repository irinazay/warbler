"""User model tests."""

import os
from unittest import TestCase

from models import db, User, Message, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"
from app import app

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        u1 = User.signup("irina", "irina@test.com", "irinapassword", None)
        u2 = User.signup("max", "max@test.com", "maxpassword", None)

        db.session.commit()

        self.u1_id=u1.id
        self.u2_id=u2.id

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        self.u1 = u1
        self.u2 = u2
        self.client = app.test_client()

    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_user_follows(self):

        follows = Follows(user_being_followed_id=self.u2.id, user_following_id=self.u1.id)
        db.session.add(follows)
        db.session.commit()


        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u2.followers), 1)
        self.assertEqual(len(self.u1.followers), 0)
        self.assertEqual(len(self.u1.following), 1)

        self.assertEqual(self.u2.followers[0].id, self.u1_id)
        self.assertEqual(self.u1.following[0].id, self.u2_id)

    def test_is_following(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))

    def test_is_followed_by(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2))


    def test_valid_signup(self):
        user = User.signup("test", "test@test.com", "password", None)
        db.session.commit()
        self.user_id = user.id

        u = User.query.get(self.user_id)
        self.u = u 

        self.assertIsNotNone(self.u)
        self.assertEqual(self.u.username, "test")
        self.assertEqual(self.u.email, "test@test.com")
        self.assertNotEqual(self.u.password, "password")
        self.assertTrue(self.u.password.startswith("$2b$"))


    def test_valid_authentication(self):
        u = User.authenticate(self.u1.username, "irinapassword")
     
        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.u1.id)
    
    def test_invalid_username(self):
        self.assertFalse(User.authenticate("anothername", "password"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.u1.username, "wrongpassword"))
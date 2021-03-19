"""Message model tests."""

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes


os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app


db.create_all()


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

   
        u = User.signup("irina", "irina@test.com", "irinapassword", None)
   
        db.session.commit()
         
        self.u_id=u.id

        user = User.query.get(self.u_id)
 
        self.user = user
        self.client = app.test_client()

    def tearDown(self):

        db.session.rollback()
  

    def test_message_model(self):
        
        m = Message(
            text="Text message",
            user_id=self.user.id
        )

        db.session.add(m)
        db.session.commit()

        self.assertEqual(len(self.user.messages), 1)
        self.assertEqual(self.user.messages[0].text, "Text message")

    def test_message_likes(self):

        m = Message(
            text="a warble",
            user_id=self.user.id
        )

        self.m = m

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)


        like = Likes(user_id=self.testuser.id, message_id=self.m.id)

        db.session.add(like)
        db.session.commit()

        l = Likes.query.filter(Likes.message_id == self.m.id).all()

        self.assertEqual(len(l), 1)
        self.assertEqual(l[0].message_id, m.id)


        
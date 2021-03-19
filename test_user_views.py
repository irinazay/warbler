import os
from unittest import TestCase
from models import db, connect_db, Message, User, Follows, Likes


os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for User."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)


        user = User(username="irinazay",
                                    email="irinazay@test.com",
                                    password="testirinazay",
                                    image_url=None)
     
        db.session.add(user)
        db.session.commit()

        self.user_id = user.id

        message1 = Message(text="This is test text message", user=user)
        
        db.session.add(message1)
        db.session.commit()

        self.message1_id = message1.id
    
        like = Likes(user_id=self.testuser.id, message_id=self.message1_id)

        db.session.add(like)
        db.session.commit()
        
        self.like = like.id

        follows = Follows(user_being_followed_id=self.user_id, user_following_id=self.testuser.id)
        db.session.add(follows)
        db.session.commit()

    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()

    def test_show_users(self):
        """List of users"""

        with app.test_client() as c:

            resp = c.get("/users")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", html)
            self.assertIn("@irinazay", html)

    def test_show_user_profile(self):
        """User profile"""

        with app.test_client() as c:

            resp = c.get(f"/users/{self.testuser.id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", html)

    def test_users_search(self):
        with app.test_client() as c:

            resp = c.get("/users?q=irina")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@irinazay", str(resp.data))


    def test_show_user_following(self):
        """List of users that this user is following"""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.testuser.id}/following")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@irinazay", html)


    def test_show_user_followers(self):
        """List of users that follows this user"""

        f = Follows(user_being_followed_id=self.testuser.id, user_following_id=self.user_id)
        db.session.add(f)
        db.session.commit()

        with app.test_client() as c:
        
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.testuser.id}/followers")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@irinazay", html)

    def test_show_user_likes(self):
        """List of liked messages"""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.testuser.id}/likes")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("This is test text message", html)
            

    def test_message_like_(self):
        """Like message for the currently-logged-in user."""

        m = Message(id=10, text="Please like my new message!", user_id=self.user_id)
        db.session.add(m)
        db.session.commit()

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/10/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==10).all()
            self.assertEqual(len(likes), 1)


    def test_message_unlike(self):
        """Toggle a liked message for the currently-logged-in user."""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/messages/{self.message1_id}/like", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            
            likes = Likes.query.filter(Likes.message_id==self.message1_id).all()
            self.assertEqual(len(likes), 0)        



    def test_show_form_to_edit_profile(self):
        """Show form to update profile for current user"""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/profile")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser", html)


    def test_to_edit_profile(self):
        """Update profile for current user"""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            d = {"image_url": "https://www.clipartkey.com/mpngs/m/22-221407_super-mario-svg-free.png", "password":"testuser"}
            resp = c.post("/users/profile", data=d, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", html)

    def test_delete_user(self):

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.post(f"/users/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@testuser", html)

    def test_stop_following(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.post(f"/users/stop-following/{self.user_id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@irinazay", html)



    def test_follow(self):
        u = User(username="max",
                                    email="max@test.com",
                                    password="testmax",
                                    image_url=None)
        db.session.add(u)
        db.session.commit()
        self.u_id =u.id

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.post(f"/users/follow/{self.u_id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@max", html)


    def test_unauthorized_following_page_access(self):

        with app.test_client() as c:

            resp = c.get(f"/users/{self.testuser.id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("irinazay", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))

    def test_unauthorized_followers_page_access(self):
        f = Follows(user_being_followed_id=self.testuser.id, user_following_id=self.user_id)
        db.session.add(f)
        db.session.commit()
        with app.test_client() as c:

            resp = c.get(f"/users/{self.testuser.id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@irinazay", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))
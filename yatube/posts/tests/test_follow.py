from django.test import TestCase, Client
from django.urls import reverse

from ..models import User, Post, Follow

AUTHOR = 'author'
FOLLOWER = 'user'
FOLLOWING_URL = reverse('posts:profile_follow',
                        kwargs={'author_name': AUTHOR})
UNFOLLOWING_URL = reverse('posts:profile_unfollow',
                        kwargs={'author_name': AUTHOR})


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=AUTHOR)
        cls.user_follow = User.objects.create_user(username=FOLLOWER)
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

    def setUp(self):
        self.follower = Client()
        self.follower.force_login(self.user_follow)

    def test_following(self):
        self.follower.get(FOLLOWING_URL)
        self.assertTrue(Follow.objects.filter(
              author=self.user, user=self.user_follow).exists())
        self.follower.get(UNFOLLOWING_URL)
        self.assertFalse(Follow.objects.filter(
              author=self.user, user=self.user_follow).exists())

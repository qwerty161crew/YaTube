from django.test import TestCase, Client
from django.urls import reverse

from ..models import User, Post

AUTHOR = 'author'
FOLLOWER = 'user'
FOLLOWING_URL = reverse('posts:profile_follow',
                        kwargs={'username': AUTHOR})


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=AUTHOR)
        cls.follower = User.objects.create_user(username=FOLLOWER)
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

    def setUp(self):
        self.author = Client()
        self.author.force_login(self.user)
        self.follower = Client()
        self.follower.force_login(self.follower)

    def test_following(self):
        self.follower.get('/profile/author/follow/')
    #     # self.assertTrue(Follow.objects.filter(
    #     #     author=self.author, user=self.follower).exists())

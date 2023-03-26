from django.test import TestCase, Client
from django.urls import reverse

from http import HTTPStatus

from ..models import Post, Group, User

AUTHOR_USERNAME = 'author'
FOLLOWER_USERNAME = 'user'
GROUP_TITLE = 'Тестовая группа'
USERNAME = 'post_author'
ANOTHER_USERNAME = 'kUZEN'
SLUG = 'test-slug'
INDEX = reverse('posts:index')
PROFILE = reverse('posts:profile',
                  kwargs={'username': USERNAME})
GROUP = reverse('posts:group_posts',
                kwargs={'slug': SLUG})
LOGIN = reverse('users:login')
CREATE = reverse('posts:post_create')
FOLLOW_INDEX_URL = reverse('posts:follow_index')
FOLLOWING_URL = reverse('posts:profile_follow',
                        kwargs={'username': AUTHOR_USERNAME})
UNFOLLOWING_URL = reverse('posts:profile_unfollow',
                          kwargs={'username': AUTHOR_USERNAME})
YOURSELF_FOLLOW_URL = reverse('posts:profile_follow',
                              kwargs={'username': FOLLOWER_USERNAME})
YOURSELF_UNFOLLOW_URL = reverse('posts:profile_unfollow',
                                kwargs={'username': FOLLOWER_USERNAME})
CREATE_LOGIN = reverse('users:login') + '?next=/create/'
LOGIN_FOLLOW = reverse('users:login') + '?next=/follow/'
UNFOLLOW = reverse('posts:profile_unfollow',
                   kwargs={'username': AUTHOR_USERNAME})
LOGIN_UNFOLLOR = reverse('users:login') + \
    f'?next=/profile/{AUTHOR_USERNAME}/unfollow/'
PROFILE_AUTHOR_URL = reverse('posts:profile',
                             kwargs={'username': AUTHOR_USERNAME})
PROFILE_FOLLOWER_URL = reverse('posts:profile',
                               kwargs={'username': FOLLOWER_USERNAME})


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.another_user = User.objects.create_user(username=ANOTHER_USERNAME)
        cls.author = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.follower = User.objects.create_user(username=FOLLOWER_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
        )
        cls.POST_EDIT = reverse('posts:post_edit',
                                kwargs={'post_id': cls.post.id})
        cls.POST_DETAIL = reverse('posts:post_detail',
                                  kwargs={'post_id': cls.post.id})
        cls.LOGIN_EDIT = reverse('users:login') + \
            f'?next=/posts/{cls.post.id}/edit/'

        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client_2 = Client()
        cls.authorized_client_2.force_login(cls.another_user)
        # cls.author_client = Client()
        # cls.author_client.force_login(cls.author)
        cls.follower_client = Client()
        cls.follower_client.force_login(cls.follower)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        CASES = [
            ['posts/index.html', INDEX, self.guest_client],
            ['posts/group_list.html', GROUP,
             self.guest_client],
            ['posts/profile.html', PROFILE,
             self.guest_client],
            ['posts/post_detail.html', self.POST_DETAIL,
             self.guest_client],
            ['posts/create_post.html', CREATE,
             self.authorized_client],
            ['posts/create_post.html',
                self.POST_EDIT,
                self.authorized_client],
            ['posts/follow.html', FOLLOW_INDEX_URL, self.authorized_client],
        ]
        for template, address, client in CASES:
            with self.subTest(address=address):
                response = client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urs_exists_at_desired_location_guest(self):
        """Проверка доступа на станицы, авторизированного пользователя и
        гостя"""
        cases = [
            [INDEX, self.guest_client, HTTPStatus.OK],
            [GROUP,
             self.guest_client, HTTPStatus.OK],
            [PROFILE, self.authorized_client, HTTPStatus.OK],
            [PROFILE,
             self.guest_client, HTTPStatus.OK],
            [CREATE,
             self.guest_client, HTTPStatus.FOUND],
            [CREATE,
             self.authorized_client, HTTPStatus.OK],
            [self.POST_EDIT,
             self.authorized_client, HTTPStatus.OK],
            [self.POST_EDIT,
             self.guest_client, HTTPStatus.FOUND],
            [self.POST_EDIT, self.authorized_client_2, HTTPStatus.FOUND],
            [FOLLOW_INDEX_URL, self.guest_client, HTTPStatus.FOUND],
            [FOLLOW_INDEX_URL, self.follower_client, HTTPStatus.OK],
            [FOLLOWING_URL, self.guest_client, HTTPStatus.FOUND],
            [FOLLOWING_URL, self.follower_client, HTTPStatus.FOUND],
            [YOURSELF_FOLLOW_URL, self.follower_client, HTTPStatus.FOUND],
            [UNFOLLOWING_URL, self.guest_client, HTTPStatus.FOUND],
            [UNFOLLOWING_URL, self.follower_client, HTTPStatus.FOUND],
            [UNFOLLOWING_URL, self.follower_client, HTTPStatus.NOT_FOUND],
        ]
        for url, client, answer in cases:
            with self.subTest(url=url, client=client, answer=answer):
                self.assertEqual(client.get(url).status_code, answer)

    def test_urls_redirects(self):
        REDIRECT_URLS = [[CREATE_LOGIN,
                          CREATE, self.guest_client],
                         [self.LOGIN_EDIT,
                          self.POST_EDIT, self.guest_client],
                         [self.POST_DETAIL, self.POST_EDIT,
                          self.authorized_client_2],
                         [LOGIN_FOLLOW, FOLLOW_INDEX_URL,
                          self.guest_client],
                         [LOGIN_UNFOLLOR,
                          UNFOLLOW, self.guest_client],
                         [PROFILE_AUTHOR_URL, FOLLOWING_URL,
                          self.follower_client],
                         [PROFILE_AUTHOR_URL, UNFOLLOWING_URL,
                          self.follower_client],
                         [PROFILE_FOLLOWER_URL, YOURSELF_FOLLOW_URL,
                          self.follower_client],
                         [PROFILE_FOLLOWER_URL, YOURSELF_UNFOLLOW_URL,
                          self.follower_client],
                         ]
        for destination, address, client in REDIRECT_URLS:
            with self.subTest(destination=destination,
                              address=address, client=client):
                response = client.get(address)
                self.assertRedirects(response, destination)

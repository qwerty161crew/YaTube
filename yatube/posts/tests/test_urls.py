from django.test import TestCase, Client
from django.urls import reverse

from http import HTTPStatus

from ..models import Post, Group, User

AUTHOR = 'author'
FOLLOWING = 'FOLLOW'
FOLLOWER = 'user'
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
FOLLOW = reverse('posts:follow_index')
FOLLOWING_URL = reverse('posts:profile_follow',
                        kwargs={'username': AUTHOR})
UNFOLLOWING_URL = reverse('posts:profile_unfollow',
                          kwargs={'username': AUTHOR})
YOURSELF_FOLLOW = reverse('posts:profile_follow',
                          kwargs={'username': FOLLOWING})
CREATE_LOGIN = reverse('users:login') + '?next=/create/'
LOGIN_FOLLOW = reverse('users:login') + '?next=/follow/'
UNFOLLOW = reverse('posts:profile_unfollow',
                          kwargs={'username': AUTHOR})
LOGIN_UNFOLLOR = reverse('users:login') + f'?next=/profile/{AUTHOR}/unfollow/'

class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follow = User.objects.create_user(username=AUTHOR)
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user_following = User.objects.create_user(username=FOLLOWING)
        cls.another_user = User.objects.create_user(username=ANOTHER_USERNAME)
        cls.user_follow = User.objects.create_user(username=FOLLOWER)
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
        cls.follower = Client()
        cls.follower.force_login(cls.user_follow)

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
            ['posts/follow.html', FOLLOW, self.authorized_client],
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
            [FOLLOW, self.guest_client, HTTPStatus.FOUND],
            [FOLLOW, self.follower, HTTPStatus.OK],
            [FOLLOWING_URL, self.guest_client, HTTPStatus.FOUND],
            [FOLLOWING_URL, self.follower, HTTPStatus.FOUND],
            [YOURSELF_FOLLOW, self.follower, HTTPStatus.FOUND],
            [UNFOLLOWING_URL, self.guest_client, HTTPStatus.FOUND],
            [UNFOLLOWING_URL, self.follower, HTTPStatus.FOUND],
        ]
        for url, client, answer in cases:
            with self.subTest(url=url, client=client, answer=answer):
                self.assertEqual(client.get(url).status_code, answer)

    def test_urls_redirects(self):
        self.REDIRECT_URLS = [[CREATE_LOGIN,
                              CREATE, self.guest_client],
                              [self.LOGIN_EDIT,
                              self.POST_EDIT, self.guest_client],
                              [self.POST_DETAIL, self.POST_EDIT,
                               self.authorized_client_2],
                              [LOGIN_FOLLOW, FOLLOW,
                               self.guest_client],
                              [LOGIN_UNFOLLOR,
                                  UNFOLLOW, self.guest_client],
                              ]
        for destination, address, client in self.REDIRECT_URLS:
            with self.subTest(destination=destination,
                              address=address, client=client):
                response = client.get(address)
                self.assertRedirects(response, destination)

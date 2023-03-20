from django.test import TestCase, Client
from django.urls import reverse

from http import HTTPStatus

from ..models import Post, Group, User

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
PROFILE_FOLLOW = reverse('posts:profile_follow', kwargs={'username': USERNAME})
PROFILE_UNFOLLOW = reverse('posts:profile_unfollow', kwargs={'username': ANOTHER_USERNAME})


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.another_user = User.objects.create_user(username=ANOTHER_USERNAME)
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
        cls.COMMENT = reverse('posts:add_comment',
                              kwargs={'post_id': cls.post.id})
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client_2 = Client()
        cls.authorized_client_2.force_login(cls.another_user)

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
            [FOLLOW, self.authorized_client, HTTPStatus.OK],
            [PROFILE_FOLLOW, self.guest_client, HTTPStatus.FOUND], 
            # [PROFILE_FOLLOW, self.authorized_client_2, HTTPStatus.OK],
            # [PROFILE_UNFOLLOW, self.guest_client, HTTPStatus.FOUND], 
            # [PROFILE_UNFOLLOW, self.authorized_client, HTTPStatus.OK],
            [self.COMMENT, self.guest_client, HTTPStatus.FOUND], 
            # [self.COMMENT, self.authorized_client_2, HTTPStatus.OK]
        ]
        for url, client, answer in cases:
            with self.subTest(url=url, client=client, answer=answer):
                self.assertEqual(client.get(url).status_code, answer)

    def test_urls_redirects(self):
        self.REDIRECT_URLS = [[f'{LOGIN}?next=/create/',
                              CREATE, self.guest_client],
                              [f'{LOGIN}?next=/posts/{self.post.id}/edit/',
                              self.POST_EDIT, self.guest_client],
                              [self.POST_DETAIL, self.POST_EDIT,
                               self.authorized_client_2],
                              [F'{LOGIN}?next=/follow/', FOLLOW,
                               self.guest_client],
                              [f'{LOGIN}?next=/posts/{self.post.id}/comment/',
                               self.COMMENT, self.guest_client],
                               [self.POST_DETAIL, self.COMMENT,
                                self.authorized_client],
                                # [f'{LOGIN}?next=/follow/', FOLLOW, self.guest_client],
                                # [FOLLOW, INDEX, self.authorized_client_2]
                              ]
        for destination, address, client in self.REDIRECT_URLS:
            with self.subTest(destination=destination, address=address, client=client):
                response = client.get(address)
                self.assertRedirects(response, destination)

import shutil
import tempfile

from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.conf import settings

from ..models import User, Post, Group, Follow
from ..settings import NUMBER_POSTS


AUTHOR = 'author'
FOLLOWER = 'user'
FOLLOWER_USERNAME = 'kUZEN'
USERNAME = 'post_author'
SLUG = 'test-slug'
SLUG_1 = 'test-slug_1'
INDEX = reverse('posts:index')
PROFILE = reverse('posts:profile',
                  kwargs={'username': USERNAME})
GROUP = reverse('posts:group_posts',
                kwargs={'slug': SLUG})
GROUP_1 = reverse('posts:group_posts',
                  kwargs={'slug': SLUG_1})
FOLLOW = reverse('posts:follow_index')
FOLLOWING_URL = reverse('posts:profile_follow',
                        kwargs={'username': AUTHOR})
UNFOLLOWING_URL = reverse('posts:profile_unfollow',
                          kwargs={'username': AUTHOR})
SMAIL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author_follow = User.objects.create_user(username=AUTHOR)
        cls.user_follow = User.objects.create_user(username=FOLLOWER)
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user_follow = User.objects.create_user(username=FOLLOWER_USERNAME)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug=SLUG,
            description='Тестовое описание',
        )
        cls.group_1 = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug_1',
            description='Тестовое описание',
        )

        cls.image_name = 'small.gif'
        cls.uploaded = SimpleUploadedFile(
            name=cls.image_name,
            content=SMAIL_GIF,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            author=cls.user_author_follow,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded
        )
        cls.POST_DETAIL = reverse('posts:post_detail',
                                  kwargs={'post_id': cls.post.id})
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.follower = Client()
        cls.follower.force_login(cls.user_follow)
        cache.clear()

    def test_post_not_in_another_feed_group(self):
        respons = self.authorized_client.get(GROUP_1)
        self.assertNotIn(self.post, respons.context['page_obj'])

    def test_post_not_in_another_feed_follow(self):
        respons = self.authorized_client.get(FOLLOW)
        self.assertNotIn(self.post, respons.context['page_obj'])

    def test_following(self):
        self.follower.get(FOLLOWING_URL)
        self.assertTrue(Follow.objects.filter(
            author=self.user_author_follow, user=self.user_follow).exists())

    def test_unfollowing(self):
        self.follower.get(UNFOLLOWING_URL)
        self.assertFalse(Follow.objects.filter(
            author=self.user_author_follow, user=self.user_follow).exists())

    def test_author_in__profile(self):
        response = self.authorized_client.get(PROFILE)
        self.assertEqual(response.context['author'], self.user)

    def test_group_in_context(self):
        response = self.authorized_client.get(GROUP)
        group = response.context['group']
        self.assertEqual(group, self.group)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(
            group.description,
            self.group.description)
        self.assertEqual(group.slug, self.group.slug)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='post_author')
        cls.follower = User.objects.create_user(username='follower')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug=SLUG,
            description='Тестовое описание',
        )
        Post.objects.bulk_create(
            Post(
                text='Тестовый текст',
                author=cls.user,
                group=cls.group,
            ) for i in range(NUMBER_POSTS + 1)
        )
        cls.guest_client = Client()
        cls.user_client = Client()
        cls.user_client.force_login(cls.follower)
        cls.follow = Follow.objects.create(
            user=cls.follower,
            author=cls.user
        )

    def test_page(self):
        urls = [
            [INDEX, NUMBER_POSTS], [GROUP, NUMBER_POSTS],
            [PROFILE, NUMBER_POSTS],
            [f'{INDEX}?page=2', 1],
            [f'{GROUP}?page=2', 1],
            [f'{PROFILE}?page=2', 1],
            [FOLLOW, NUMBER_POSTS],
            [f'{FOLLOW}?page=2', 1]
        ]
        cache.clear()
        for url, number in urls:
            with self.subTest(url=url):
                self.assertEqual(len(self.user_client.get(
                    url).context.get('page_obj')),
                    number
                )

    def test_index_page_caching(self):
        response1 = self.guest_client.get(INDEX)
        Post.objects.create(
            author=self.follower,
            text='Тестовый текст',
            group=self.group,
        )
        response2 = self.guest_client.get(INDEX)
        cache.clear()
        response3 = self.guest_client.get(INDEX)
        self.assertEqual(response1.content, response2.content)
        self.assertNotEqual(response2.content, response3.content)


class TestViewClass(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.authorized_user = User.objects.create_user(username='user_2')
        cls.group = Group.objects.create(
            title='32',
            slug=SLUG,
            description='32'
        )
        cls.group_2 = Group.objects.create(
            title='23',
            slug=SLUG_1,
            description='23'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMAIL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='text',
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )
        cls.follow = Follow.objects.create(
            author=cls.user,
            user=cls.authorized_user,
        )

        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.id}
        )

        cls.guest = Client()
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.another = Client()
        cls.another.force_login(cls.authorized_user)

        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_show_correct_context(self):
        """Страницы сформированы с корректным контекстом"""
        url_pages = [
            INDEX,
            GROUP,
            PROFILE,
            FOLLOW,
        ]
        for url in url_pages:
            with self.subTest(url=url):
                response = self.another.get(url)
                if 'page_obj' in response.context:
                    self.assertEqual(len(response.context['page_obj']), 1)
                    post = response.context['page_obj'][0]
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.id, self.post.id)
                self.assertEqual(post.image, self.post.image)

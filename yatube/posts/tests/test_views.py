from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import User, Post, Group
from ..settings import NUMBER_POSTS


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
PROFILE_FOLLOW = reverse('posts:profile_follow', kwargs={
                         'author_name': USERNAME})
PROFILE_UNFOLLOW = reverse('posts:profile_unfollow', kwargs={
                           'author_name': FOLLOWER_USERNAME})


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image_name = 'small.gif'
        cls.uploaded = SimpleUploadedFile(
            name=cls.image_name,
            content=small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded
        )
        cls.POST_DETAIL = reverse('posts:post_detail',
                                  kwargs={'post_id': cls.post.id})
        cls.COMMENT = reverse('posts:add_comment',
                              kwargs={'post_id': cls.post.id})
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.follower = Client()
        cls.follower.force_login(cls.user_follow)

    def test_post_not_in_another_group(self):
        response = self.authorized_client.get(GROUP_1)
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_post_in_group(self):
        responses = [
            [INDEX, 'page_obj'],
            [GROUP, 'page_obj'],
            [PROFILE, 'page_obj'],
            [self.POST_DETAIL, 'post'],
            # [FOLLOW, 'page_obj']
        ]
        for url, obj in responses:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                if obj == 'page_obj':
                    posts = response.context[obj]
                    self.assertEqual(len(posts), 1)
                    post = posts[0]
                elif obj == 'post':
                    post = response.context['post']
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.pk, self.post.pk)

    # def test_author_in__profile(self):
    #     response = self.authorized_client.get(PROFILE)
    #     self.assertEqual(response.context['author'], self.user)

    def test_group_in_context(self):
        response = self.authorized_client.get(GROUP)
        self.assertEqual(response.context['group'], self.group)
        self.assertEqual(response.context['group'].title, self.group.title)
        self.assertEqual(response.context['group'].slug, self.group.slug)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='post_author')
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

    def setUp(self):
        self.guest_client = Client()

    def test_page(self):
        urls = [
            [INDEX, NUMBER_POSTS], [GROUP, NUMBER_POSTS],
            [PROFILE, NUMBER_POSTS],
            [f'{INDEX}?page=2', 1],
            [f'{GROUP}?page=2', 1],
            [f'{PROFILE}?page=2', 1],
            # [f'{FOLLOW}?page=2', 1][FOLLOW, NUMBER_POSTS],
        ]
        for url, number in urls:
            with self.subTest(url=url):
                self.assertEqual(len(self.guest_client.get(
                    url).context.get('page_obj')),
                    number
                )

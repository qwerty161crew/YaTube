from django.test import TestCase, Client
from django.urls import reverse

from ..models import User, Post, Group
from ..settings import NUMBER_POSTS

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


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )
        cls.POST_DETAIL = reverse('posts:post_detail',
                                  kwargs={'post_id': cls.post.id})

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_not_in_another_group(self):
        response = self.authorized_client.get(GROUP_1)
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_post_in_group(self):
        responses = [
            [INDEX, 'page_obj'],
            [GROUP, 'page_obj'],
            [PROFILE, 'page_obj'],
            [self.POST_DETAIL, 'post'],
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

    def test_author_in__profile(self):
        response = self.authorized_client.get(PROFILE)
        self.assertEqual(response.context['author'], self.user)

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
                group=cls.group
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
            [f'{PROFILE}?page=2', 1]
        ]
        for url, number in urls:
            with self.subTest(url=url):
                self.assertEqual(len(self.guest_client.get(
                    url).context.get('page_obj')),
                    number
                )

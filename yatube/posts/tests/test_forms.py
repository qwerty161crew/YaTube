from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from ..forms import forms
from ..models import Group, Post, User

USERNAME = 'tester'
PROFILE = reverse('posts:profile', kwargs={'username': USERNAME})
CREATE_POST = reverse('posts:post_create')
SMAIL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
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
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded
        )
        cls.authorized_client = Client()  # Авторизованный
        cls.authorized_client.force_login(cls.user)
        cls.EDIT_POST = reverse('posts:post_edit',
                                kwargs={'post_id': cls.post.id})
        cls.POST_DETAIL = reverse('posts:post_detail',
                                  kwargs={'post_id': cls.post.id})

    def test_create_post(self):
        form_data = {
            'text': 'text',
            'group': self.group.pk,
            'file': self.uploaded,
            'author': USERNAME
        }
        """Тестирование создания поста"""
        post_count_initial = Post.objects.count()
        self.authorized_client.post(
            CREATE_POST,
            data=form_data,
        )
        self.assertEqual(Post.objects.count(), post_count_initial + 1)
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        # self.assertEqual(post.image, type(self.uploaded))
        self.assertEqual(post.author, self.user)
        # self.assertEqual(Post.objects.count())

    def test_editing_post(self):
        form_data = {
            'text': 'TEST',
            'group': self.group_1.pk,
            'file': self.uploaded
        }
        response = self.authorized_client.post(
            self.EDIT_POST,
            data=form_data,
            follow=True
        )
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(form_data['group'], post.group.id)
        self.assertEqual(USERNAME, self.user.username)
        self.assertRedirects(response, self.POST_DETAIL)

    def test_post_posts_edit_page_show_correct_context(self):
        templates_url_names = [
            self.EDIT_POST,
            CREATE_POST,
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for url in templates_url_names:
            response = self.authorized_client.get(url)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(
                        value)
                    self.assertIsInstance(form_field, expected)

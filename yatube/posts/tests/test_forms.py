from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from http import HTTPStatus

from ..forms import forms
from ..models import Group, Post, User


USERNAME_EDIT_NOT_AUTHOR = 'Llily'
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
        cls.user_not_aythor = User.objects.create_user(
            username=USERNAME_EDIT_NOT_AUTHOR)
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
        cls.guest_client = Client()
        cls.authorized_client = Client()  # Авторизованный
        cls.authorized_client.force_login(cls.user)
        cls.not_author = Client()
        cls.not_author.force_login(cls.user_not_aythor)
        cls.EDIT_POST = reverse('posts:post_edit',
                                kwargs={'post_id': cls.post.id})
        cls.POST_DETAIL = reverse('posts:post_detail',
                                  kwargs={'post_id': cls.post.id})
        cls.COMMENT = reverse('posts:add_comment', kwargs={
                              'post_id': cls.post.id})
        Post.objects.create(
            text="Этот пост будет использован для проверки "
            "работы страницы редактирования поста",
            author=cls.user,
            group=cls.group,
        )
        cls.EDIT_POST_NOT_AUTHOR = reverse('posts:post_edit', kwargs={
                                           'post_id': cls.post.id}
                                           )

    def test_create_post(self):
        form_data = {
            'text': 'text',
            'group': self.group.pk,
            'file': self.uploaded,
        }
        """Тестирование создания поста"""
        post_count_initial = Post.objects.count()
        self.authorized_client.post(
            CREATE_POST,
            data=form_data,
        )
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(self.image_name, self.image_name)
        self.assertEqual(post.author, self.user)
        self.assertEqual(Post.objects.count(), post_count_initial + 1)

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
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author.username, self.user.username)
        self.assertRedirects(response, self.POST_DETAIL)

    def test_comment_post_form(self):
        form_data_auth = {
            'text': 'Коммент аторизированного пользователя'
        }
        form_data_guest = {
            'text': 'Коммент неавторизованного пользователя'
        }
        self.authorized_client.post(
            self.COMMENT,
            data=form_data_auth,
            follow=True,
        )
        comm_count_auth = self.post.comments.count()
        self.assertEqual(comm_count_auth, 1, 'Коммент не отправился')
        self.guest_client.post(
            self.COMMENT,
            data=form_data_guest,
            follow=True,
        )
        comm_count_guest = self.post.comments.count()
        self.assertEqual(comm_count_guest, 1, 'Коммент отправился')

    def test_post_posts_edit_not_author(self):
        templates_url_names = [
            self.EDIT_POST_NOT_AUTHOR,
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

    def test_invalid_form(self):
        """Некорректная форма не создает/не редактирует пост."""
        posts_count = Post.objects.count()
        not_existing_group_id = -1
        form_pieces_of_data = (
            {
                "text": ""
            },
            {
                "text": "Этот не должно попасть в БД",
                "group": not_existing_group_id
            },
        )
        urls = (
            (CREATE_POST, HTTPStatus.OK),
            (
                self.EDIT_POST,
                HTTPStatus.OK),

        )
        for url, request_code in urls:
            for form_data in form_pieces_of_data:
                with self.subTest(
                    url=url, request_code=request_code, form_data=form_data
                ):
                    response = self.not_author.post(
                        path=url, data=form_data, follow=True
                    )
                    self.assertEqual(Post.objects.count(), posts_count)
                    self.assertEqual(response.status_code, request_code)

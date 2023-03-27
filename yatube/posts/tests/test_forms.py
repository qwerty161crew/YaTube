from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile


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
        cls.user_not_author = User.objects.create_user(
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
        cls.not_author.force_login(cls.user_not_author)
        cls.EDIT_POST = reverse('posts:post_edit',
                                kwargs={'post_id': cls.post.id})
        cls.POST_DETAIL = reverse('posts:post_detail',
                                  kwargs={'post_id': cls.post.id})
        cls.COMMENT = reverse('posts:add_comment', kwargs={
                              'post_id': cls.post.id})
        cls.EDIT_POST_NOT_AUTHOR = reverse('posts:post_edit', kwargs={
                                           'post_id': cls.post.id}
                                           )

    def test_create_post(self):
        form_data = {
            'text': 'text',
            'group': self.group.pk,
            'file': self.uploaded,
        }
        post_count_initial = Post.objects.count()
        self.authorized_client.post(
            CREATE_POST,
            data=form_data,
        )
        Post.objects.filter(text=form_data['text'],
                            group=form_data['group'],
                            image=form_data['file'],
                            author=self.user)
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
        self.assertEqual(post.author.username, self.post.author.username)
        self.assertRedirects(response, self.POST_DETAIL)

    def test_comment_post_form(self):
        self.form_data_auth = {
            'text': 'Коммент аторизированного пользователя'
        }
        self.form_data_guest = {
            'text': 'Коммент неавторизованного пользователя'
        }
        self.authorized_client.post(
            self.COMMENT,
            data=self.form_data_auth,
            follow=True,
        )
        comm_count_auth = self.post.comments.count()
        self.assertEqual(comm_count_auth, 1, 'Коммент не отправился')
        self.guest_client.post(
            self.COMMENT,
            data=self.form_data_guest,
            follow=True,
        )
        comm_count_guest = self.post.comments.count()
        self.assertEqual(comm_count_guest, 1, 'Коммент отправился')

    def test_post_edit(self):
        url_names = [
            self.EDIT_POST_NOT_AUTHOR,
            CREATE_POST,
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for url in url_names:
            response = self.authorized_client.get(url)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(
                        value)
                    self.assertIsInstance(form_field, expected)

    def test_invalid_form(self):
        form_data = {
            'text': 'TEST_2',
            'group': self.group_1.pk,
            'file': self.uploaded
        }
        response = self.not_author.post(
            self.EDIT_POST,
            data=form_data,
            follow=True,
        )
        post = Post.objects.get(id=self.post.id)
        self.assertNotEqual(form_data['text'], post.text)
        self.assertNotEqual(form_data['group'], post.group.id)
        self.assertNotEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author.username, self.user.username)
        self.assertRedirects(response, self.POST_DETAIL)

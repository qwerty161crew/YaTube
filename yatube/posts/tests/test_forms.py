from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile


from ..forms import forms
from ..models import Group, Post, User, Comment


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
LOGIN = reverse('users:login')


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
            text='text',
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
        cls.LOGIN_COMMENT = f'{LOGIN}?next={cls.COMMENT}'
        cls.LOGIN_EDIT = f'{LOGIN}?next={cls.EDIT_POST}'

    def test_create_post(self):
        Post.objects.all().delete()
        image_name = 'some.self_create_image'
        uploaded = SimpleUploadedFile(
            name=image_name,
            content=SMAIL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'text_test',
            'group': self.group.pk,
            'image': uploaded,
        }
        respons = self.authorized_client.post(
            CREATE_POST,
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), 1)
        post_create = Post.objects.get()
        self.assertEqual(form_data['text'], post_create.text)
        test_image_short_name = form_data['image'].name.split('.')[0]
        self.assertEqual(
            f"posts/{test_image_short_name}",
            post_create.image.name.split('.')[0])
        self.assertEqual(form_data['group'], post_create.group.id)
        self.assertEqual(post_create.author.username,
                         self.post.author.username)
        self.assertRedirects(respons, PROFILE)

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
        test_image_short_name = form_data['file'].name.split('.')[0]
        self.assertEqual(
            f"posts/{test_image_short_name}",
            post.image.name.split('.')[0])
        self.assertEqual(form_data['group'], post.group.id)
        self.assertEqual(post.author.username, self.post.author.username)
        self.assertRedirects(response, self.POST_DETAIL)

    def test_comment_post_form(self):
        Comment.objects.all().delete()
        self.form_data_auth = {
            'text': 'Коммент аторизированного пользователя'
        }

        self.authorized_client.post(
            self.COMMENT,
            data=self.form_data_auth,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.get()
        self.assertEqual(comment.post_id, self.post.id)
        self.assertEqual(self.form_data_auth['text'], comment.text)
        self.assertEqual(self.user.username, comment.author.username)

    def test_post_edit(self):
        url_names = [
            self.EDIT_POST_NOT_AUTHOR,
            CREATE_POST,
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.ImageField
        }
        for url in url_names:
            response = self.authorized_client.get(url)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(
                        value)
                    self.assertIsInstance(form_field, expected)

    def test_comment_guest(self):
        clients = ((self.guest_client, self.LOGIN_EDIT),
                   (self.not_author, self.POST_DETAIL))
        form_data = {
            'text': 'TEST_2',
            'group': self.group_1.pk,
            'file': self.uploaded
        }
        for client, adress in clients:
            response = client.post(
                self.EDIT_POST,
                data=form_data,
                follow=True,
            )
            post = Post.objects.get(id=self.post.id)
            self.assertEqual(post.author.username, self.user.username)
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(
                str(form_data['file']).split('.')[0],
                str(self.image_name.split('.')[0]))
            self.assertEqual(post.group, self.post.group)
            self.assertRedirects(response, adress)

    def test_commit_field(self):
        Post.objects.all().delete()
        self.form_data_guest = {
            'text': 'Коммент неавторизованного пользователя'
        }
        response = self.guest_client.post(
            self.COMMENT,
            data=self.form_data_guest,
            follow=True,
        )
        self.assertRedirects(response, self.LOGIN_COMMENT)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(0, Comment.objects.all().count())

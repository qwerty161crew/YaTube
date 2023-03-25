from django.test import TestCase

from ..models import Group, Post, User, Comment, Follow
from ..settings import SLICE


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.author = User.objects.create_user(username='avtor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост который состоит из 15 сиволов',
            author=cls.user,
        )
        cls.comment = Comment(
            post=cls.post,
            author=cls.user,
            text='Тестовый коммент объёмом больше пятнадцати символов',
        )
        cls.follow = Follow(
            user=cls.user,
            author=cls.author
        )

    def test_models_have_correct_object_names(self):
        """__str__  task - это строчка с содержимым task.title."""
        post = PostModelTest.post  # Обратите внимание на синтаксис
        expected_object_name = post.text[:SLICE]
        self.assertEqual(expected_object_name, str(post))

    def test_models_group(self):
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_comment_model(self):
        comment = PostModelTest.comment
        expected_object_name = comment.text[:SLICE]
        self.assertEqual(expected_object_name, str(comment))

    def test_following_model(self):
        following = PostModelTest.follow
        following_str = f'{str(self.user)} {str(self.author)}'
        self.assertEqual(str(following), following_str)

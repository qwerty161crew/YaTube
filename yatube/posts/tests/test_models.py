from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост который состоит из 15 сиволов',
            author=cls.user,
        )

    def test_models_have_correct_object_names(self):
        """__str__  task - это строчка с содержимым task.title."""
        post = PostModelTest.post  # Обратите внимание на синтаксис
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

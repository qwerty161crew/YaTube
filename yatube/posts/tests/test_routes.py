from django.test import TestCase
from django.urls import reverse

POST_ID = 1
USERNAME = 'auth'
SLUG = 'test-slug'
CASES = [
    ['/', 'index', None],
    [f'/group/{SLUG}/', 'group_posts', [SLUG]],
    [f'/profile/{USERNAME}/', 'profile', [USERNAME]],
    [f'/posts/{POST_ID}/', 'post_detail', [POST_ID]],
    ['/create/', 'post_create', None],
    [f'/posts/{POST_ID}/edit/', 'post_edit', [POST_ID]],
]


class PostUrlTests(TestCase):
    def test_urls_uses_correct_route(self):

        for url, name, args in CASES:
            self.assertEqual(url, reverse(f'posts:{name}', args=args))

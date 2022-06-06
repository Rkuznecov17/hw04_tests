from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='hasnoname')
        cls.group = Group.objects.create(
            title='Название группы для теста',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        cls.group_wihtout_posts = Group.objects.create(
            title='Название группы без постов для теста',
            slug='test-withou_posts-slug',
            description='Тестовое описание группы без постов'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст для поста',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_with_posts_show_correct_context(self):
        """Шаблоны index, group_list и profile сформированы
        с правильным контекстом.
        """
        templates_page_names = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.post.author}),
        }
        for reverse_name in templates_page_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIn(self.post, response.context.get('page_obj'))

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        self.assertEqual(
            response.context['post'].text, 'Тестовый текст для поста'
        )

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_appears_on_pages(self):
        """
        Созданный пост появляется на страницах:
        index, group_list, profile.
        """
        urls = (
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': 'hasnoname'}),
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.author, self.user)
                self.assertEqual(first_object.text,
                                 'Тестовый текст для поста'
                                 )
                self.assertEqual(first_object.group.title,
                                 'Название группы для теста'
                                 )

    def test_no_post_in_another_group_page(self):
        """Проверка, что пост не появляется на странице другой группы"""
        test_post = Post.objects.order_by('-pk')[0]
        another_group = Group.objects.exclude(id=test_post.group.id)[0]
        response = self.guest_client.get(reverse(
            'posts:group_list', kwargs={'slug': another_group.slug}))
        posts = response.context['page_obj']
        self.assertNotIn(test_post, posts)

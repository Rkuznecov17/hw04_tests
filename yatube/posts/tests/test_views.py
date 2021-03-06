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

    def common_test(self, post, text, group, author):
        if text:
            self.assertEqual(post.text, self.post.text)
        if group:
            self.assertEqual(post.group.title, self.group.title)
        if author:
            self.assertEqual(post.author, self.post.author)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        TaskPagesTests.common_test(
            self,
            post,
            text=True,
            group=True,
            author=True
        )

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        post = response.context['page_obj'][0]
        TaskPagesTests.common_test(
            self,
            post,
            text=True,
            group=True,
            author=False
        )

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        post = response.context['page_obj'][0]
        TaskPagesTests.common_test(
            self,
            post,
            text=True,
            group=False,
            author=True
        )

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
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
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
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
            reverse('posts:profile', kwargs={'username': self.user}),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                post = response.context['page_obj'][0]
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group.title, self.post.group.title)

    def test_no_post_in_another_group_page(self):
        """Проверка, что пост не появляется на странице другой группы"""
        response = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group_wihtout_posts.slug}))
        posts = response.context['page_obj']
        self.assertEqual(0, len(posts))

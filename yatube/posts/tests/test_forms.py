from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='hasnoname')
        cls.another_user = User.objects.create_user(username='noname')
        cls.group = Group.objects.create(
            title='Название группы для теста',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        cls.edited_group = Group.objects.create(
            title='Название группы после редактирования',
            slug='test-edited',
            description='Тестовое описание группы после редактирования'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст для поста',
            group=cls.group,
        )
        cls.form = PostForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_form_post_create_post(self):
        """
        Проверяем, что при отправке валидной формы со страницы
        создания поста reverse('posts:create_post')
        создаётся новая запись в базе данных.
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст для поста',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст для поста',
                group=self.group
            ).exists()
        )

    def test_form_post_edit_post(self):
        """
        Проверяем, что при отправке валидной формы со страницы
        редактирования поста reverse('posts:post_edit', args=('post_id',))
        происходит изменение поста с post_id в базе данных.
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст для поста',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        first_post = Post.objects.first()
        self.assertEqual(
            first_post.text,
            'Тестовый текст для поста'
        )
        self.assertEqual(
            first_post.group.title,
            'Название группы для теста'
        )

    def test_form_post_edit_post_by_anonym(self):
        """
        Редактирование под анонимом (пост не должен изменить значения полей).
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста, отредактированного анонимом.',
            'group': self.edited_group.id,
        }
        response = self.client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('users:login') + '?next='
            + reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        edited_post = Post.objects.get(id=self.post.id)
        self.assertNotEqual(edited_post.text, form_data['text'])
        self.assertNotEqual(edited_post.group.id, form_data['group'])

    def test_form_post_edit_post_by_noname(self):
        """
        Редактирование не автором (пост не должен изменить значения полей).
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста, отредактированного не автором.',
            'group': self.edited_group.id,
        }
        self.authorized_client.force_login(self.another_user)
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        edited_post = Post.objects.get(id=self.post.id)
        self.assertNotEqual(edited_post.text, form_data['text'])
        self.assertNotEqual(edited_post.group.id, form_data['group'])

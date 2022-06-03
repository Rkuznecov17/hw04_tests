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
        cls.group_1 = Group.objects.create(
            title='Название группы_1 для теста',
            slug='test-slug_1',
            description='Тестовое описание группы_1'
        )
        cls.post_1 = Post.objects.create(
            author=cls.user,
            text='Тестовый текст для поста_1',
            group=cls.group_1,
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
            'text': 'Тестовый текст для поста_1',
            'group': self.group_1.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': 'hasnoname'})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст для поста_1',
                group=self.group_1
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
            'text': 'Тестовый текст для поста_1',
            'group': self.group_1.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': '1'}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(
            Post.objects.first().text,
            'Тестовый текст для поста_1'
        )
        self.assertEqual(
            Post.objects.first().group.title,
            'Название группы_1 для теста'
        )

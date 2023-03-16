from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField(_('заголовок'), max_length=200)
    slug = models.SlugField(_('идентификатор'), unique=True)
    description = models.TextField(_('описание'))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('Группа')
        verbose_name_plural = _('Группы')


class Post(CreatedModel):
    text = models.TextField(_('текст'))
    pub_date = models.DateTimeField(_('дата публикации'), auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='автор'
    )
    group = models.ForeignKey(
        Group, on_delete=models.SET_NULL,
        related_name='posts', blank=True, null=True, verbose_name='группа')

    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = _('Пост')
        verbose_name_plural = _('Посты')

class Comment(CreatedModel):

    post = models.ForeignKey(
            Post,
            on_delete=models.CASCADE,
            related_name='comments',
            verbose_name='комментарий'
    )
    created = models.DateTimeField(_('дата публикации'), auto_now_add=True)

    text = models.TextField(_('текст'))

    class Meta:
        ordering = ['-created']
        verbose_name = ('Коммент')
        verbose_name_plural = ('Комменты')

class Follow(models.Model):
    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = ('Подписка')
        verbose_name_plural = ('Подписки')
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'
            ),
        )

from pathlib import Path
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.templatetags.static import static


def avatar_upload_path(instance, filename):
    """Генерирует неперебираемое имя файла аватарки в MEDIA_ROOT/avatars/."""
    ext = Path(filename).suffix.lower() or '.png'
    return f'avatars/{uuid.uuid4().hex}{ext}'


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь',
    )
    nickname = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Никнейм',
    )
    avatar = models.ImageField(
        upload_to=avatar_upload_path,
        blank=True,
        null=True,
        verbose_name='Аватар',
    )

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return self.nickname or self.user.username

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return static('core/img/author1.png')

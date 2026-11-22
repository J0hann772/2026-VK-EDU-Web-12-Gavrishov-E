from django.contrib.auth.models import User

from .models import Tag


def sidebar_data(request):
    # В админке сайдбар сайта не нужен — не делаем лишние запросы
    if request.path.startswith('/admin/'):
        return {}

    return {
        'popular_tags': Tag.objects.all()[:10],
        'best_members': User.objects.select_related('profile').all()[:5],
    }

from django.contrib.auth.models import User
from django.templatetags.static import static

from core.models import Profile

from .models import Tag


def sidebar_data(request):
    # В админке сайдбар сайта не нужен — не делаем лишние запросы
    if request.path.startswith('/admin/'):
        return {}

    context = {
        'popular_tags': Tag.objects.all()[:10],
        'best_members': User.objects.select_related('profile').all()[:5],
    }

    if request.user.is_authenticated:
        profile = Profile.objects.filter(user=request.user).first()
        context['current_user_avatar'] = (
            profile.get_avatar_url() if profile else static('core/img/author1.png')
        )
        context['current_user_name'] = (
            profile.nickname if (profile and profile.nickname) else request.user.username
        )

    return context

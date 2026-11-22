from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name = 'Профиль'
    verbose_name_plural = 'Профиль'


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('id', 'username', 'email', 'get_nickname', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'profile__nickname')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile')

    @admin.display(description='Никнейм')
    def get_nickname(self, obj):
        profile = getattr(obj, 'profile', None)
        return profile.nickname if profile else ''


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'nickname', 'avatar')
    list_filter = ('user__is_active', 'user__is_staff')
    search_fields = ('user__username', 'user__email', 'nickname')
    raw_id_fields = ('user',)
    list_select_related = ('user',)

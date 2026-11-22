from django.contrib import admin

from .models import Answer, AnswerLike, Question, QuestionLike, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name',)


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    raw_id_fields = ('author',)
    fields = ('author', 'text', 'is_correct', 'rating')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'rating', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'text', 'author__username')
    raw_id_fields = ('author', 'tags')
    list_select_related = ('author',)
    inlines = (AnswerInline,)
    show_full_result_count = False


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'author', 'is_correct', 'rating', 'created_at')
    list_filter = ('is_correct', 'created_at')
    search_fields = ('text', 'author__username', 'question__title')
    raw_id_fields = ('question', 'author')
    list_select_related = ('question', 'author')
    show_full_result_count = False


@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'question', 'value', 'created_at')
    list_filter = ('value', 'created_at')
    search_fields = ('user__username', 'question__title')
    raw_id_fields = ('user', 'question')
    list_select_related = ('user', 'question')
    show_full_result_count = False


@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'answer', 'value', 'created_at')
    list_filter = ('value', 'created_at')
    search_fields = ('user__username', 'answer__text')
    raw_id_fields = ('user', 'answer')
    list_select_related = ('user', 'answer')
    show_full_result_count = False

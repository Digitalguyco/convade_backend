from django.contrib import admin
from .models import (
    HelpCategory, Article, FAQ, SupportTicket, TicketMessage,
    ContentRating, HelpSearch, KnowledgeBase
)


@admin.register(HelpCategory)
class HelpCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    search_fields = ('name',)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'is_featured')
    search_fields = ('title', 'content')


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question_short', 'category', 'is_active')
    search_fields = ('question', 'answer')
    
    def question_short(self, obj):
        return obj.question[:50] + "..." if len(obj.question) > 50 else obj.question


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('requester', 'subject', 'status', 'priority')
    search_fields = ('subject', 'requester__email')


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'author', 'message_type')
    search_fields = ('author__email', 'content')


@admin.register(ContentRating)
class ContentRatingAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'user')
    search_fields = ('user__email',)


@admin.register(HelpSearch)
class HelpSearchAdmin(admin.ModelAdmin):
    list_display = ('query', 'user')
    search_fields = ('query', 'user__email')


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ('is_public',)
    search_fields = ('content',)

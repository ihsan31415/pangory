from django.contrib import admin
from .models import DiscussionPost, DiscussionReply

class DiscussionReplyInline(admin.TabularInline):
    model = DiscussionReply
    extra = 0

@admin.register(DiscussionPost)
class DiscussionPostAdmin(admin.ModelAdmin):
    list_display = ('topic', 'course', 'author', 'created_at', 'reply_count')
    list_filter = ('course', 'created_at')
    search_fields = ('topic', 'content', 'author__email')
    inlines = [DiscussionReplyInline]

@admin.register(DiscussionReply)
class DiscussionReplyAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'created_at')
    list_filter = ('post__course', 'created_at')
    search_fields = ('content', 'author__email', 'post__topic')

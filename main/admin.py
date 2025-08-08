from django.contrib import admin
from .models import Article, Session, Playlist, Media, Submission


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author_name', 'status', 'article_type', 'featured', 'created_at', 'views']
    list_filter = ['status', 'article_type', 'created_at']
    search_fields = ['title', 'author_name', 'description']
    list_editable = ['status', 'featured']
    readonly_fields = ['views', 'created_at', 'updated_at']


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'author_name', 'status', 'session_type', 'featured', 'created_at', 'views']
    list_filter = ['status', 'session_type', 'created_at']
    search_fields = ['title', 'author_name', 'description']
    list_editable = ['status', 'featured']
    readonly_fields = ['views', 'created_at', 'updated_at']


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ['title', 'author_name', 'status', 'platform', 'featured', 'track_count', 'created_at']
    list_filter = ['status', 'platform', 'created_at']
    search_fields = ['title', 'author_name', 'description']
    list_editable = ['status', 'featured']
    readonly_fields = ['views', 'created_at', 'updated_at']


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ['title', 'author_name', 'status', 'media_type', 'featured', 'created_at', 'views']
    list_filter = ['status', 'media_type', 'created_at']
    search_fields = ['title', 'author_name', 'description']
    list_editable = ['status', 'featured']
    readonly_fields = ['views', 'created_at', 'updated_at']


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['title', 'author_name', 'content_type', 'created_at', 'reviewed', 'approved']
    list_filter = ['content_type', 'reviewed', 'approved', 'created_at']
    search_fields = ['title', 'author_name', 'description']
    list_editable = ['reviewed', 'approved']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(reviewed=False)

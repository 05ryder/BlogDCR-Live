from django.db import models
from django.utils import timezone
# from tinymce.models import HTMLField  # Temporarily disabled


class ContentStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PUBLISHED = 'published', 'Published'
    ARCHIVED = 'archived', 'Archived'
    PRIVATE = 'private', 'Private'
    REJECTED = 'rejected', 'Rejected'


class ContentType(models.TextChoices):
    ARTICLE = 'article', 'Article/Interview'
    SESSION = 'session', 'Session'
    PLAYLIST = 'playlist', 'Playlist'
    PHOTOGRAPHY = 'photography', 'Photography'
    ARTWORK = 'artwork', 'Artwork/Media'
    EVENT = 'event', 'Event Coverage'


class BaseContent(models.Model):
    """Base model for all content types"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    author_name = models.CharField(max_length=100)
    author_email = models.EmailField()
    author_class_year = models.CharField(max_length=4, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ContentStatus.choices,
        default=ContentStatus.PENDING
    )
    content_type = models.CharField(
        max_length=20,
        choices=ContentType.choices
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    # Custom publication date for archival imports and manual date setting
    custom_publication_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Set a custom publication date for archival content or backdating"
    )
    views = models.PositiveIntegerField(default=0)
    featured = models.BooleanField(default=False)
    homepage_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-custom_publication_date', '-published_at', '-created_at']
        abstract = True
    
    def get_display_date(self):
        """Returns the most appropriate date for display purposes"""
        if self.custom_publication_date:
            return self.custom_publication_date
        elif self.published_at:
            return self.published_at.date()
        else:
            return self.created_at.date()


class Article(BaseContent):
    """Articles and Interviews"""
    content = models.TextField()  # Temporarily using TextField instead of HTMLField
    excerpt = models.CharField(max_length=300, blank=True)
    cover_image = models.ImageField(upload_to='articles/', blank=True)
    article_type = models.CharField(
        max_length=20,
        choices=[
            ('interview', 'Interview'),
            ('feature', 'Feature'),
            ('review', 'Review'),
            ('news', 'News')
        ],
        default='feature'
    )
    
    def __str__(self):
        return self.title


class Session(BaseContent):
    """Live Sessions and DJ Sets"""
    session_type = models.CharField(
        max_length=20,
        choices=[
            ('live', 'Live Performance'),
            ('dj_set', 'DJ Set'),
            ('interview', 'Interview Session')
        ]
    )
    location = models.CharField(max_length=100, blank=True)  # e.g., "Robinson Hall"
    video_url = models.URLField(blank=True)
    audio_url = models.URLField(blank=True)
    cover_image = models.ImageField(upload_to='sessions/', blank=True)
    content = models.TextField(blank=True)  # Temporarily using TextField instead of HTMLField
    
    def __str__(self):
        return self.title


class Playlist(BaseContent):
    """Student-curated playlists"""
    platform = models.CharField(
        max_length=20,
        choices=[
            ('spotify', 'Spotify'),
            ('soundcloud', 'SoundCloud'),
            ('youtube', 'YouTube')
        ]
    )
    playlist_url = models.URLField()
    track_count = models.PositiveIntegerField(default=0)
    duration = models.CharField(max_length=20, blank=True)
    cover_color = models.CharField(max_length=7, default='#000000')  # Hex color for mockup
    
    # Rich metadata fields
    platform_id = models.CharField(max_length=100, blank=True)  # Spotify ID, SoundCloud track ID, etc.
    embed_html = models.TextField(blank=True)  # Cached embed HTML
    creator_name = models.CharField(max_length=100, blank=True)  # Platform username/artist
    genre = models.CharField(max_length=50, blank=True)
    
    def save(self, *args, **kwargs):
        # Auto-generate embed HTML and extract metadata when saving
        if self.playlist_url:
            from main.utils.music_platforms import generate_music_embed, extract_playlist_metadata
            
            # Generate embed HTML
            self.embed_html = generate_music_embed(self.playlist_url) or ''
            
            # Extract metadata
            metadata = extract_playlist_metadata(self.playlist_url)
            if metadata:
                self.platform_id = metadata.get('spotify_id', '')
                if metadata.get('creator') and not self.creator_name:
                    self.creator_name = metadata['creator']
        
        super().save(*args, **kwargs)
    
    def get_embed_html(self):
        """Get embed HTML, generating if not cached"""
        if not self.embed_html and self.playlist_url:
            from main.utils.music_platforms import generate_music_embed
            self.embed_html = generate_music_embed(self.playlist_url) or ''
            self.save(update_fields=['embed_html'])
        return self.embed_html
    
    def __str__(self):
        return self.title


class Media(BaseContent):
    """Photos, Artwork, Videos"""
    media_type = models.CharField(
        max_length=20,
        choices=[
            ('photography', 'Photography'),
            ('artwork', 'Artwork'),
            ('poster', 'Poster'),
            ('video', 'Video')
        ]
    )
    file = models.FileField(upload_to='media_files/')
    file_size = models.CharField(max_length=20, blank=True)  # e.g., "245 MB"
    dimensions = models.CharField(max_length=20, blank=True)  # e.g., "1920x1080"
    
    def __str__(self):
        return self.title


class Submission(models.Model):
    """Student submissions before approval"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    author_name = models.CharField(max_length=100)
    author_email = models.EmailField()
    author_class_year = models.CharField(max_length=4, blank=True)
    content_type = models.CharField(
        max_length=20,
        choices=ContentType.choices
    )
    
    # Content-specific fields
    content_text = models.TextField(blank=True)  # For articles
    playlist_url = models.URLField(blank=True)  # For playlists
    platform = models.CharField(max_length=20, blank=True)  # For playlists
    files = models.FileField(upload_to='submissions/', blank=True)  # For media
    
    created_at = models.DateTimeField(default=timezone.now)
    reviewed = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.author_name}"


class HomepageConfig(models.Model):
    """Configuration for homepage content and layout"""
    
    # Featured Content
    featured_article = models.ForeignKey(
        Article, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='featured_on_homepage'
    )
    
    # Featured Content Customization
    featured_title = models.CharField(
        max_length=200, 
        blank=True, 
        help_text="Custom title for featured content (overrides article title)"
    )
    featured_description = models.TextField(
        blank=True, 
        help_text="Custom description for featured content (overrides article description)"
    )
    featured_button_text = models.CharField(
        max_length=50, 
        default="Read Full Interview", 
        help_text="Text for the call-to-action button (e.g., 'Read Interview', 'Watch Here', 'Listen Here')"
    )
    featured_image = models.ImageField(
        upload_to='featured/', 
        blank=True, 
        null=True, 
        help_text="Custom image for featured content (auto-resized to fit layout)"
    )
    
    # Section Configuration
    show_featured_section = models.BooleanField(default=True)
    show_sessions_section = models.BooleanField(default=True)
    show_playlists_section = models.BooleanField(default=True)
    
    # Content Limits
    sessions_count = models.PositiveIntegerField(default=3, help_text="Number of sessions to show")
    playlists_count = models.PositiveIntegerField(default=4, help_text="Number of playlists to show")
    
    # Section Ordering
    sections_order = models.JSONField(
        default=list,
        help_text="Order of sections: ['featured', 'sessions', 'playlists']"
    )
    
    # Custom Content
    hero_title = models.CharField(max_length=200, blank=True, help_text="Custom hero title")
    hero_subtitle = models.TextField(blank=True, help_text="Custom hero subtitle")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = "Homepage Configuration"
        verbose_name_plural = "Homepage Configurations"
    
    def save(self, *args, **kwargs):
        # Ensure default sections order
        if not self.sections_order:
            self.sections_order = ['featured', 'sessions', 'playlists']
        super().save(*args, **kwargs)
    
    @classmethod
    def get_current(cls):
        """Get or create the current homepage configuration"""
        config, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'sections_order': ['featured', 'sessions', 'playlists'],
                'sessions_count': 3,
                'playlists_count': 3,
            }
        )
        return config
    
    def __str__(self):
        return f"Homepage Config (Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"


class FeaturedContent(models.Model):
    """Track featured content across the site"""
    
    CONTENT_TYPES = [
        ('article', 'Article'),
        ('session', 'Session'),
        ('playlist', 'Playlist'),
        ('media', 'Media'),
    ]
    
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    object_id = models.PositiveIntegerField()
    
    # Feature settings
    featured_on_homepage = models.BooleanField(default=False)
    featured_in_section = models.BooleanField(default=False)
    priority = models.PositiveIntegerField(default=0, help_text="Higher numbers appear first")
    
    # Metadata
    featured_at = models.DateTimeField(auto_now_add=True)
    featured_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['-priority', '-featured_at']
        unique_together = ['content_type', 'object_id']
    
    def get_content_object(self):
        """Get the actual content object"""
        model_map = {
            'article': Article,
            'session': Session,
            'playlist': Playlist,
            'media': Media,
        }
        model = model_map.get(self.content_type)
        if model:
            try:
                return model.objects.get(id=self.object_id)
            except model.DoesNotExist:
                return None
        return None
    
    def __str__(self):
        obj = self.get_content_object()
        if obj:
            return f"Featured {self.content_type}: {obj.title}"
        return f"Featured {self.content_type} (ID: {self.object_id})"

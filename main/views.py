from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Article, Session, Playlist, Media, Submission, ContentStatus


# Public Views
def homepage(request):
    """Simple test homepage to verify Django routing"""
    from django.http import HttpResponse
    return HttpResponse("""
    <html>
    <head><title>BlogDCR - Test</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1 style="color: #00693E;">🎉 BlogDCR is LIVE! 🎉</h1>
        <p>Django routing is working!</p>
        <p>Railway deployment successful!</p>
        <p><a href="/admin/">Admin Panel</a> | <a href="/about/">About</a></p>
    </body>
    </html>
    """)


def features(request):
    """Features page with articles and interviews"""
    articles = Article.objects.filter(status=ContentStatus.PUBLISHED)
    context = {'articles': articles}
    return render(request, 'main/features.html', context)


def sessions(request):
    """Sessions page with live performances and DJ sets"""
    sessions = Session.objects.filter(status=ContentStatus.PUBLISHED)
    context = {'sessions': sessions}
    return render(request, 'main/sessions.html', context)


def playlists(request):
    """Playlists page with student-curated playlists"""
    playlists = Playlist.objects.filter(status=ContentStatus.PUBLISHED)
    context = {'playlists': playlists}
    return render(request, 'main/playlists.html', context)


def media_gallery(request):
    """Enhanced media gallery with dashboard functionality"""
    media_type = request.GET.get('type', 'all')
    
    # Get all published media for stats
    all_media = Media.objects.filter(status=ContentStatus.PUBLISHED)
    
    # Calculate statistics
    stats = {
        'total': all_media.count(),
        'photography': all_media.filter(media_type='photography').count(),
        'artwork': all_media.filter(media_type='artwork').count(),
        'posters': all_media.filter(media_type='poster').count(),
        'videos': all_media.filter(media_type='video').count(),
    }
    
    # Filter media items based on selected type
    if media_type == 'all':
        media_items = all_media.order_by('-custom_publication_date', '-published_at', '-created_at')
    else:
        media_items = all_media.filter(media_type=media_type).order_by('-custom_publication_date', '-published_at', '-created_at')
    
    context = {
        'media_items': media_items,
        'current_filter': media_type,
        'stats': stats,
    }
    return render(request, 'main/media.html', context)


@require_http_methods(["POST"])
@login_required
def toggle_media_status(request, media_id):
    """Toggle media status between published and private"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    try:
        media_item = Media.objects.get(id=media_id)
        
        # Toggle status
        if media_item.status == ContentStatus.PUBLISHED:
            media_item.status = ContentStatus.PRIVATE
            action = 'hidden'
        else:
            media_item.status = ContentStatus.PUBLISHED
            action = 'published'
        
        media_item.save()
        
        return JsonResponse({
            'success': True, 
            'new_status': media_item.status,
            'action': action
        })
        
    except Media.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Media not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def about(request):
    """About page with WDCR information"""
    return render(request, 'main/about.html')


def submit_content(request):
    """Student submission form"""
    if request.method == 'POST':
        # Create submission from form data
        submission = Submission.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            author_name=request.POST.get('author_name'),
            author_email=request.POST.get('author_email'),
            author_class_year=request.POST.get('author_class_year', ''),
            content_type=request.POST.get('content_type'),
            content_text=request.POST.get('content_text', ''),
            playlist_url=request.POST.get('playlist_url', ''),
            platform=request.POST.get('platform', ''),
        )
        
        # Handle file uploads
        if 'files' in request.FILES:
            submission.files = request.FILES['files']
            submission.save()
        
        messages.success(request, 'Your submission has been received and will be reviewed by our editorial team.')
        return redirect('main:homepage')
    
    return render(request, 'main/submit.html')


# Editor Views
def editor_login(request):
    """Editor authentication"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('main:dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions.')
    
    return render(request, 'main/editor_login.html')


@login_required
def editor_logout(request):
    """Editor logout"""
    logout(request)
    return redirect('main:homepage')


@login_required
def editor_dashboard(request):
    """Editor dashboard with overview"""
    if not request.user.is_superuser:
        return redirect('main:homepage')
    
    pending_count = Submission.objects.filter(reviewed=False).count()
    approved_today = Submission.objects.filter(
        approved=True,
        created_at__date=timezone.now().date()
    ).count()
    
    context = {
        'pending_count': pending_count,
        'approved_today': approved_today,
    }
    return render(request, 'main/dashboard.html', context)


@login_required
def pending_submissions(request):
    """Pending submissions for review"""
    if not request.user.is_superuser:
        return redirect('main:homepage')
    
    submissions = Submission.objects.filter(reviewed=False)
    context = {'submissions': submissions}
    return render(request, 'main/submissions.html', context)


@login_required
def published_content(request):
    """Published content management"""
    if not request.user.is_superuser:
        return redirect('main:homepage')
    
    articles = Article.objects.filter(status=ContentStatus.PUBLISHED)
    sessions = Session.objects.filter(status=ContentStatus.PUBLISHED)
    playlists = Playlist.objects.filter(status=ContentStatus.PUBLISHED)
    media = Media.objects.filter(status=ContentStatus.PUBLISHED)
    
    context = {
        'articles': articles,
        'sessions': sessions,
        'playlists': playlists,
        'media': media,
    }
    return render(request, 'main/published.html', context)





# API Views
@csrf_exempt
def approve_submission(request, submission_id):
    """Approve a submission and convert to published content"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Create appropriate content type based on submission
    if submission.content_type == 'article':
        Article.objects.create(
            title=submission.title,
            description=submission.description,
            author_name=submission.author_name,
            author_email=submission.author_email,
            author_class_year=submission.author_class_year,
            content_type=submission.content_type,
            content=submission.content_text,
            status=ContentStatus.PUBLISHED,
            published_at=timezone.now()
        )
    elif submission.content_type == 'playlist':
        Playlist.objects.create(
            title=submission.title,
            description=submission.description,
            author_name=submission.author_name,
            author_email=submission.author_email,
            author_class_year=submission.author_class_year,
            content_type=submission.content_type,
            playlist_url=submission.playlist_url,
            platform=submission.platform,
            status=ContentStatus.PUBLISHED,
            published_at=timezone.now()
        )
    elif submission.content_type in ['session', 'interview']:
        Session.objects.create(
            title=submission.title,
            description=submission.description,
            author_name=submission.author_name,
            author_email=submission.author_email,
            author_class_year=submission.author_class_year,
            content_type=submission.content_type,
            status=ContentStatus.PUBLISHED,
            published_at=timezone.now()
        )
    elif submission.content_type in ['artwork', 'photography', 'media']:
        Media.objects.create(
            title=submission.title,
            description=submission.description,
            author_name=submission.author_name,
            author_email=submission.author_email,
            author_class_year=submission.author_class_year,
            content_type=submission.content_type,
            status=ContentStatus.PUBLISHED,
            published_at=timezone.now()
        )
    else:
        # Default to Article for any other content type
        Article.objects.create(
            title=submission.title,
            description=submission.description,
            author_name=submission.author_name,
            author_email=submission.author_email,
            author_class_year=submission.author_class_year,
            content_type=submission.content_type,
            content=submission.content_text or submission.description,
            status=ContentStatus.PUBLISHED,
            published_at=timezone.now()
        )
    
    # Mark submission as reviewed and approved
    submission.reviewed = True
    submission.approved = True
    submission.save()
    
    return JsonResponse({'success': True})


@csrf_exempt
def reject_submission(request, submission_id):
    """Reject a submission"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    submission = get_object_or_404(Submission, id=submission_id)
    submission.reviewed = True
    submission.approved = False
    submission.save()
    
    return JsonResponse({'success': True})


@login_required
def preview_submission(request, submission_id):
    """Preview a submission before approval"""
    if not request.user.is_superuser:
        return redirect('main:homepage')
    
    submission = get_object_or_404(Submission, id=submission_id)
    
    context = {
        'submission': submission,
        'is_preview': True,
    }
    
    # Render preview based on content type
    if submission.content_type == 'article':
        return render(request, 'main/preview_article.html', context)
    elif submission.content_type == 'playlist':
        return render(request, 'main/preview_playlist.html', context)
    elif submission.content_type in ['photography', 'artwork']:
        return render(request, 'main/preview_media.html', context)
    else:
        return render(request, 'main/preview_generic.html', context)


@login_required
@csrf_exempt
def toggle_content_visibility(request, content_type, content_id):
    """Toggle visibility of published content"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    model_map = {
        'article': Article,
        'session': Session,
        'playlist': Playlist,
        'media': Media,
    }
    
    if content_type not in model_map:
        return JsonResponse({'error': 'Invalid content type'}, status=400)
    
    model = model_map[content_type]
    content = get_object_or_404(model, id=content_id)
    
    # Toggle between published and private
    if content.status == ContentStatus.PUBLISHED:
        content.status = ContentStatus.PRIVATE
    else:
        content.status = ContentStatus.PUBLISHED
    
    content.save()
    return JsonResponse({'success': True})


@login_required
@csrf_exempt
def delete_content(request, content_type, content_id):
    """Delete published content"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    model_map = {
        'article': Article,
        'session': Session,
        'playlist': Playlist,
        'media': Media,
    }
    
    if content_type not in model_map:
        return JsonResponse({'error': 'Invalid content type'}, status=400)
    
    model = model_map[content_type]
    content = get_object_or_404(model, id=content_id)
    content.delete()
    
    return JsonResponse({'success': True})


@login_required
def edit_content(request, content_type, content_id):
    """Edit published content"""
    if not request.user.is_superuser:
        return redirect('main:homepage')
    
    model_map = {
        'article': Article,
        'session': Session,
        'playlist': Playlist,
        'media': Media,
    }
    
    if content_type not in model_map:
        return redirect('main:published')
    
    model = model_map[content_type]
    content = get_object_or_404(model, id=content_id)
    
    if request.method == 'POST':
        # Update content fields
        content.title = request.POST.get('title')
        content.description = request.POST.get('description')
        content.status = request.POST.get('status')
        
        # Handle custom publication date
        custom_date = request.POST.get('custom_publication_date')
        if custom_date:
            from datetime import datetime
            content.custom_publication_date = datetime.strptime(custom_date, '%Y-%m-%d').date()
        else:
            content.custom_publication_date = None
        
        # Content-type specific fields
        if content_type == 'article':
            content.content = request.POST.get('content')
        elif content_type == 'playlist':
            content.playlist_url = request.POST.get('playlist_url')
            content.platform = request.POST.get('platform')
        elif content_type == 'session':
            content.session_type = request.POST.get('session_type')
            content.video_url = request.POST.get('video_url')
            content.content = request.POST.get('content')  # Rich text content
        
        content.save()
        return JsonResponse({'success': True})
    
    context = {
        'content': content,
        'content_type': content_type,
    }
    
    return render(request, 'main/edit_content.html', context)


@login_required
def homepage_editor(request):
    """Homepage editor for managing dynamic content"""
    if not request.user.is_superuser:
        return redirect('main:homepage')
    
    from main.models import HomepageConfig, FeaturedContent
    
    # Get or create homepage configuration
    config = HomepageConfig.get_current()
    
    if request.method == 'POST':
        # Handle configuration updates
        action = request.POST.get('action')
        
        if action == 'update_config':
            config.show_featured_section = request.POST.get('show_featured_section') == 'on'
            config.show_sessions_section = request.POST.get('show_sessions_section') == 'on'
            config.show_playlists_section = request.POST.get('show_playlists_section') == 'on'
            config.hero_title = request.POST.get('hero_title', '')
            config.hero_subtitle = request.POST.get('hero_subtitle', '')
            config.updated_by = request.user
            config.save()
            
        elif action == 'set_featured_article':
            article_id = request.POST.get('article_id')
            if article_id:
                try:
                    article = Article.objects.get(id=article_id, status=ContentStatus.PUBLISHED)
                    config.featured_article = article
                    config.updated_by = request.user
                    config.save()
                except Article.DoesNotExist:
                    pass
                    
        elif action == 'update_featured_content':
            # Handle comprehensive featured content updates
            article_id = request.POST.get('featured_article_id')
            if article_id:
                try:
                    article = Article.objects.get(id=article_id, status=ContentStatus.PUBLISHED)
                    config.featured_article = article
                except Article.DoesNotExist:
                    pass
            
            # Update custom featured content fields
            config.featured_title = request.POST.get('featured_title', '')
            config.featured_description = request.POST.get('featured_description', '')
            config.featured_button_text = request.POST.get('featured_button_text', 'Read Full Interview')
            
            # Handle image upload
            if 'featured_image' in request.FILES:
                config.featured_image = request.FILES['featured_image']
            elif request.POST.get('remove_image') == 'true':
                if config.featured_image:
                    config.featured_image.delete()
                    config.featured_image = None
            
            config.updated_by = request.user
            config.save()
        
        elif action == 'update_sections_order':
            sections_order = request.POST.getlist('sections_order')
            config.sections_order = sections_order
            config.updated_by = request.user
            config.save()
        
        return JsonResponse({'success': True})
    
    # Get content for the editor
    context = {
        'config': config,
        'available_articles': Article.objects.filter(status=ContentStatus.PUBLISHED).order_by('-published_at')[:10],
        'latest_sessions': Session.objects.filter(status=ContentStatus.PUBLISHED).order_by('-published_at')[:config.sessions_count],
        'fresh_playlists': Playlist.objects.filter(status=ContentStatus.PUBLISHED).order_by('-published_at')[:config.playlists_count],
        'featured_content': FeaturedContent.objects.all()[:10],
        # Content library for featured content editor
        'all_articles': Article.objects.filter(status=ContentStatus.PUBLISHED).order_by('-published_at'),
        'all_sessions': Session.objects.filter(status=ContentStatus.PUBLISHED).order_by('-published_at'),
        'all_playlists': Playlist.objects.filter(status=ContentStatus.PUBLISHED).order_by('-published_at'),
        'all_interviews': Article.objects.filter(status=ContentStatus.PUBLISHED, article_type='interview').order_by('-published_at'),
    }
    
    return render(request, 'main/homepage_editor.html', context)


@login_required
@csrf_exempt
def feature_content(request, content_type, content_id):
    """Feature/unfeature content for homepage"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    from main.models import FeaturedContent
    
    # Toggle featured status
    featured, created = FeaturedContent.objects.get_or_create(
        content_type=content_type,
        object_id=content_id,
        defaults={
            'featured_on_homepage': True,
            'featured_by': request.user,
            'priority': 1
        }
    )
    
    if not created:
        featured.featured_on_homepage = not featured.featured_on_homepage
        featured.featured_by = request.user
        featured.save()
    
    return JsonResponse({
        'success': True,
        'featured': featured.featured_on_homepage
    })


@login_required
@csrf_exempt
def tinymce_upload_image(request):
    """Handle image uploads for TinyMCE rich text editor"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST' and request.FILES.get('file'):
        import os
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        
        uploaded_file = request.FILES['file']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if uploaded_file.content_type not in allowed_types:
            return JsonResponse({'error': 'Invalid file type'}, status=400)
        
        # Validate file size (max 5MB)
        if uploaded_file.size > 5 * 1024 * 1024:
            return JsonResponse({'error': 'File too large'}, status=400)
        
        # Generate unique filename
        import uuid
        file_extension = os.path.splitext(uploaded_file.name)[1]
        filename = f"tinymce/{uuid.uuid4()}{file_extension}"
        
        # Save file
        file_path = default_storage.save(filename, ContentFile(uploaded_file.read()))
        file_url = default_storage.url(file_path)
        
        return JsonResponse({
            'location': request.build_absolute_uri(file_url)
        })
    
    return JsonResponse({'error': 'No file provided'}, status=400)

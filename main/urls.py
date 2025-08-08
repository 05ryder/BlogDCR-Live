from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    # Public pages
    path('', views.homepage, name='homepage'),
    path('features/', views.features, name='features'),
    path('sessions/', views.sessions, name='sessions'),
    path('playlists/', views.playlists, name='playlists'),
    path('media/', views.media_gallery, name='media'),
    path('about/', views.about, name='about'),
    
    # Submission system
    path('submit/', views.submit_content, name='submit'),
    
    # Editor authentication
    path('webdcr/', views.editor_login, name='editor_login'),
    path('dashboard/', views.editor_dashboard, name='dashboard'),
    path('logout/', views.editor_logout, name='logout'),
    
    # Content management
    path('submissions/', views.pending_submissions, name='submissions'),
    path('published/', views.published_content, name='published'),
    path('homepage-editor/', views.homepage_editor, name='homepage_editor'),
    
    # API endpoints for AJAX
    path('api/approve/<int:submission_id>/', views.approve_submission, name='approve_submission'),
    path('api/reject/<int:submission_id>/', views.reject_submission, name='reject_submission'),
    path('api/preview/<int:submission_id>/', views.preview_submission, name='preview_submission'),
    path('api/toggle/<str:content_type>/<int:content_id>/', views.toggle_content_visibility, name='toggle_content_visibility'),
    path('api/delete/<str:content_type>/<int:content_id>/', views.delete_content, name='delete_content'),
    path('api/media/<int:media_id>/toggle-status/', views.toggle_media_status, name='toggle_media_status'),
    path('edit/<str:content_type>/<int:content_id>/', views.edit_content, name='edit_content'),
    path('api/feature/<str:content_type>/<int:content_id>/', views.feature_content, name='feature_content'),
    
    # TinyMCE image upload
    path('tinymce/upload-image/', views.tinymce_upload_image, name='tinymce_upload_image'),
]

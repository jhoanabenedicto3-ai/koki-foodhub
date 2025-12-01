"""
URL configuration for koki_foodhub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# koki_foodhub/urls.py
from django.contrib import admin
from django.urls import path, include
from core import views as core_views
from core.login_view import login
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path
from django.http import HttpResponse
import os

def media_file_view(request, path):
    """Safely serve media files, return 404 if not found"""
    import mimetypes
    from django.http import FileResponse
    
    media_root = str(settings.MEDIA_ROOT)
    file_path = os.path.join(media_root, path)
    
    # Security check: ensure the file is within MEDIA_ROOT
    real_path = os.path.abspath(file_path)
    real_root = os.path.abspath(media_root)
    
    if not real_path.startswith(real_root):
        return HttpResponse(status=403)
    
    # Check if file exists
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        # Return a 404 response instead of crashing
        return HttpResponse(b'Not Found', status=404)
    
    # Try to serve the file
    try:
        response = FileResponse(open(file_path, 'rb'))
        # Guess the content type
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type:
            response['Content-Type'] = content_type
        return response
    except Exception as e:
        import logging
        logging.error(f'Error serving media file {path}: {str(e)}')
        return HttpResponse(b'Error', status=500)

urlpatterns = [
    path("admin/", admin.site.urls),
    # Auth
    path("login/", login, name="login"),
    path("logout/", core_views.logout_view, name="logout"),
    path("profile/", core_views.profile, name="profile"),
    # App
    path("", include("core.urls")),
    
]

# Serve media files
if settings.DEBUG:
    # Development: use Django's static() helper
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Production: use custom view that handles missing files gracefully
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', media_file_view),
    ]

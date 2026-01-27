"""
Improved login view with error handling and debugging
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.views.decorators.http import require_http_methods
import logging

logger = logging.getLogger(__name__)

@require_http_methods(["GET", "POST"])
def login(request):
    """Custom login view with better error handling"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not username or not password:
            messages.error(request, 'Username and password are required')
            return render(request, 'pages/login.html')
        
        try:
            # Authenticate user
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    # Login successful
                    auth_login(request, user)
                    # Redirect to 'next' parameter if provided, else dashboard
                    next_url = request.GET.get('next', 'dashboard')
                    return redirect(next_url)
                else:
                    messages.error(request, 'Your account is inactive. Please contact an administrator.')
                    logger.warning(f"Login attempt with inactive account: {username}")
                    return render(request, 'pages/login.html')
            else:
                messages.error(request, 'Invalid username or password')
                logger.info(f"Failed login attempt for username: {username}")
                return render(request, 'pages/login.html')
        
        except Exception as e:
            # Prefer to not expose internal DB errors or tracebacks to end users.
            # If this is a database OperationalError, show a user-friendly message.
            try:
                from django.db.utils import OperationalError as DBOperationalError
                if isinstance(e, DBOperationalError):
                    logger.exception(f"Login error (DB unreachable) for user {username}: {e}")
                    messages.error(request, 'Service temporarily unavailable. Please try again in a few minutes.')
                else:
                    logger.exception(f"Login error for user {username}: {e}")
                    messages.error(request, 'Login error. Please try again or contact support.')
            except Exception:
                # Fallback: generic message and log
                logger.exception(f"Login error for user {username}: {e}")
                messages.error(request, 'Login error. Please try again or contact support.')
    
    return render(request, 'pages/login.html')

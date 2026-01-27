#!/usr/bin/env python
"""
Create a debug/status endpoint to check login and user status
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

# This is a script to add a debug endpoint - let's modify urls to include it

print("Creating debug endpoint...")

# Let's just output what we should add to urls.py
debug_view_code = '''
def debug_status(request):
    """Debug endpoint to check authentication status"""
    from django.http import JsonResponse
    
    return JsonResponse({
        'authenticated': request.user.is_authenticated,
        'username': request.user.username if request.user.is_authenticated else None,
        'user_id': request.user.id if request.user.is_authenticated else None,
        'session_key': request.session.session_key,
        'debug': {
            'request_method': request.method,
            'request_path': request.path,
            'has_session': bool(request.session.session_key),
            'cookies': list(request.COOKIES.keys()),
        }
    }, indent=2)
'''

print("DEBUG VIEW CODE TO ADD:")
print(debug_view_code)
print("\nAnd add to koki_foodhub/urls.py:")
print('    path("api/debug/status/", debug_views.debug_status, name="api_debug_status"),')

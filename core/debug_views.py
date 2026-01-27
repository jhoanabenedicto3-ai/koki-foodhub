"""Debug views for troubleshooting"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def debug_status(request):
    """Debug endpoint to check authentication and session status"""
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

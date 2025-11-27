from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

def group_required(*group_names):
    """
    Requires user to be in any of the specified groups OR be staff/superuser.
    """
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if user.is_superuser or user.is_staff:
                return view_func(request, *args, **kwargs)
            if user.groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("You do not have permission to access this resource.")
        return _wrapped
    return decorator

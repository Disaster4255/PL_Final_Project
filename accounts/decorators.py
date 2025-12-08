from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from functools import wraps

def role_required(*roles):
    """
    Decorator to check if user has one of the specified roles
    Usage: @role_required('ADMIN', 'STRATEGIST')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            
            if hasattr(request.user, 'profile') and request.user.profile.role in roles:
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied("You don't have permission to access this page.")
        return wrapper
    return decorator

def admin_required(view_func):
    """Decorator for admin-only views"""
    return role_required('ADMIN')(view_func)

def strategist_or_admin_required(view_func):
    """Decorator for strategist or admin views"""
    return role_required('ADMIN', 'STRATEGIST')(view_func)

def scouter_required(view_func):
    """Decorator for scouter views (all roles can scout)"""
    return role_required('ADMIN', 'STRATEGIST', 'SCOUTER')(view_func)

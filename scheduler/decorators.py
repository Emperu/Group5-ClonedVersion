from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def login_required(view_func):
    """Decorator to require login for a view"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'user_id' not in request.session:
            messages.error(request, 'Please login to access this page')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(*allowed_roles):
    """Decorator to require specific role(s) for a view"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if 'user_id' not in request.session:
                messages.error(request, 'Please login to access this page')
                return redirect('login')

            user_role = request.session.get('user_role')
            if user_role not in allowed_roles:
                messages.error(request, f'Access denied. This page is only for {", ".join(allowed_roles)}s.')
                return redirect('home')

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
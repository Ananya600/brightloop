from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    def deco(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            u = request.user
            if not (u.is_superuser or u.role in roles):
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return login_required(wrapper)
    return deco
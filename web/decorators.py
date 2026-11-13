
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def roles_permitidos(*roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if (
                request.user.is_superuser
                or request.user.rol == 'ADMINISTRADOR'
                or request.user.rol in roles
            ):
                return view_func(request, *args, **kwargs)

            messages.error(
                request,
                'No tienes permisos para acceder a esta sección.'
            )
            return redirect('dashboard')

        return wrapper
    return decorator

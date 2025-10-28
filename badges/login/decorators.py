from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import user_passes_test

def role_required(required_role):
    def check_role(user):
        return user.is_authenticated and user.role == required_role
    return user_passes_test(check_role)

# Альтернативный вариант - декоратор для представлений
def teacher_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'teacher':
            return HttpResponseForbidden("Доступ только для педагогов")
        return view_func(request, *args, **kwargs)
    return wrapper

def student_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'student':
            return HttpResponseForbidden("Доступ только для учеников")
        return view_func(request, *args, **kwargs)
    return wrapper
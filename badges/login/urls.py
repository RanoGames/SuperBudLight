from django.urls import path
from . import views

app_name = 'login'  # опционально, но полезно для namespacing

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('home/', views.home_view, name='home'),
]
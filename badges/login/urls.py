from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'login'

urlpatterns = [
    path('', views.landing_view, name='landing.html'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('home/', views.home_view, name='home'),
]

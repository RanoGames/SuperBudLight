from django.urls import path
from . import views

app_name = 'ratings'

urlpatterns = [
    path('rating/', views.rating_view, name='rating'),
    path('artel-rating/', views.artel_rating_view, name='artel_rating'),
    path('my-artel-rating/', views.my_artel_rating_view, name='my_artel_rating'),
]

from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.shop_view, name='shop'),
    path('buy/<int:item_id>/', views.buy_item_view, name='buy_item'),
]

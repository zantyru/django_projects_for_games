from django.urls import path
from .admin import admin_site
from . import views


app_name = "game_triangle_racer"

urlpatterns = [
    path('', views.GameClientView.as_view(), name='client'),
    path('api/start/', views.StartAPI.as_view(), name='api-start'),
    path('api/pull/<str:token>/', views.PullAPI.as_view(), name='api-pull'),
    path('api/push/<str:token>/', views.PushAPI.as_view(), name='api-push'),
    path('api/shop/<str:token>/', views.ShopAPI.as_view(), name='api-shop'),
]

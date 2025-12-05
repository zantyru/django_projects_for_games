from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("app_dummy_index.urls")),
    path("game_triangle_racer/", include("game_triangle_racer.urls")),
]

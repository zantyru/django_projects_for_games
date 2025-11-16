from django.urls import path
from app_dummy_index import views


app_name = "app_dummy_index"

urlpatterns = [
    path("", views.index, name="index"),
]
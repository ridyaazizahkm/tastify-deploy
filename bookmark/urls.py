from django.urls import path
from . import views

urlpatterns = [
    path('', views.bookmark_list, name='bookmark_list'),
    path('add/<int:recipe_id>/', views.add_bookmark, name='add_bookmark'),
    path('remove/<int:recipe_id>/', views.remove_bookmark, name='remove_bookmark'),
]
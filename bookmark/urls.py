from django.urls import path
from . import views

app_name = 'bookmark'

urlpatterns = [
    path('', views.bookmark_list, name='list_bookmark'),
    path('toggle/<int:resep_id>/', views.toggle_bookmark, name='toggle_bookmark'),
    path('check/<int:resep_id>/', views.check_bookmark_status, name='check_bookmark_status'), 
]

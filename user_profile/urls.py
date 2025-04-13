from django.urls import path
from user_profile.views import profile, profile_detail
from . import views

app_name = 'user_profile'

urlpatterns = [
    path('', profile, name='profile'),
    path('edit/', profile_detail, name='profile_detail'),
    path('resep/<int:pk>/', views.resep_detail, name='resep_detail'),
]
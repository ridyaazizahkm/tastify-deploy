from django.urls import path
from .views import add_rating

app_name = 'rating'

urlpatterns = [
    path('add_rating/<int:resep_id>/', add_rating, name='add_rating'),
]

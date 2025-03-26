from django.urls import path
from .views import list_resep, create_resep, detail_resep

app_name = 'resep'

urlpatterns = [
    path('', list_resep, name='list_resep'),
    path('create/', create_resep, name='create_resep'),
    path('<int:id>/', detail_resep, name='detail_resep'),
]

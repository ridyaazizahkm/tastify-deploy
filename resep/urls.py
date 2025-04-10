from django.urls import path
from .views import list_resep, create_resep, detail_resep, edit_resep, delete_resep

app_name = 'resep'

urlpatterns = [
    path('', list_resep, name='list_resep'),
    path('create/', create_resep, name='create_resep'),
    path('detail/<int:id>/', detail_resep, name='detail_resep'),
    path('edit/<int:id>/', edit_resep, name='edit_resep'),
    path('delete/<int:id>/', delete_resep, name='delete_resep'),
]

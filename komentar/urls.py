from django.urls import path
from . import views

app_name = 'komentar'  

urlpatterns = [
    path('add/<int:resep_id>/', views.add_komentar, name='add_komentar'),
    path('delete/<int:komentar_id>/', views.delete_komentar, name='delete_komentar'),
]
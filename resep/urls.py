from django.urls import path
from .views import admin_moderate_recipe, list_resep, create_resep, detail_resep, edit_resep, delete_resep, report_recipe

app_name = 'resep'

urlpatterns = [
    path('', list_resep, name='list_resep'),
    path('create/', create_resep, name='create_resep'),
    path('detail/<int:id>/', detail_resep, name='detail_resep'),
    path('edit/<int:id>/', edit_resep, name='edit_resep'),
    path('delete/<int:id>/', delete_resep, name='delete_resep'),
    path('report/<int:recipe_id>/', report_recipe, name='report_recipe'),
    path('admin-moderate/<int:recipe_id>/', admin_moderate_recipe, name='admin_moderate_recipe'),
]

from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.show_main, name='show_main'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/reports/delete/<int:report_id>/', views.delete_comment, name='delete_comment'),
    path('admin-dashboard/reports/ignore/<int:report_id>/', views.ignore_report, name='ignore_report'),
    path('admin-dashboard/users/ban/<int:user_id>/', views.ban_user, name='ban_user'),
    path('admin-dashboard/reports/clear-history/', views.clear_report_history, name='clear_report_history'),
    path('admin-dashboard/recipe-reports/delete/<int:report_id>/', views.delete_recipe, name='delete_recipe'),
    path('admin-dashboard/recipe-reports/ignore/<int:report_id>/', views.ignore_recipe_report, name='ignore_recipe_report'),
]
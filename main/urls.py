from django.urls import path
from main.views import show_main, admin_dashboard

app_name = 'main'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard')

]
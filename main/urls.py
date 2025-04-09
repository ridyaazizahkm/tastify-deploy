from django.urls import path
from main.views import approve_report, decline_report, ban_user, show_main, admin_dashboard
app_name = 'main'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/reports/approve/<int:report_id>/', approve_report, name='approve_report'),
    path('admin-dashboard/reports/decline/<int:report_id>/', decline_report, name='decline_report'),
    path('admin-dashboard/users/ban/<int:user_id>/', ban_user, name='ban_user'),
]
from django.shortcuts import render, redirect, get_object_or_404
from resep.models import Resep
from django.contrib.auth.decorators import login_required, user_passes_test
from authentication.models import UserProfile
from django.contrib.auth.models import User
from komentar.models import Report, Komentar
from django.contrib import messages

def show_main(request):
    latest_recipes = Resep.objects.select_related('kategori', 'metode_masak', 'bahan_utama').all().order_by('-id')[:5]
    context = {
        "user": request.user,
        "latest_recipes": latest_recipes,
    }
    return render(request, "main.html", context)

def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    user_profiles = UserProfile.objects.select_related('user').all()
    reported_comments = Report.objects.select_related('reporter', 'comment', 'comment__user').all().order_by('-created_at')
    return render(request, 'admin_dashboard.html', {
        'user_profiles': user_profiles, 
        'reported_comments': reported_comments
    })

@login_required
@user_passes_test(is_admin)
def approve_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    
    if request.method == 'POST':
        report.status = 'approved'
        report.save()
        
        comment = report.comment
        comment.delete()
        
        messages.success(request, 'Report approved and comment removed.')
    
    return redirect('main:admin_dashboard')

@login_required
@user_passes_test(is_admin)
def decline_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    
    if request.method == 'POST':
        report.status = 'declined'
        report.save()
        
        messages.success(request, 'Report declined.')
    
    return redirect('main:admin_dashboard')

@login_required
@user_passes_test(is_admin)
def ban_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.is_active = False
        user.save()
        
        user_reports = Report.objects.filter(comment__user=user, status='pending')
        for report in user_reports:
            report.status = 'approved'
            report.save()

        try:
            profile = UserProfile.objects.get(user=user)
            profile.save()
        except UserProfile.DoesNotExist:
            pass
        
        messages.success(request, f'User {user.username} has been banned.')
    
    return redirect('main:admin_dashboard')
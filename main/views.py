from django.shortcuts import render, redirect, get_object_or_404
from resep.models import Resep
from rating.models import Rating
from authentication.models import AdminAccessLog
from django.contrib.auth.decorators import login_required, user_passes_test
from authentication.models import UserProfile
from django.db.models import Avg, Count, F
import random
from django.utils import timezone
from django.contrib.auth.models import User
from komentar.models import Report, Komentar
from django.contrib import messages

def show_main(request):
    latest_recipes = Resep.objects.select_related('kategori', 'metode_masak', 'bahan_utama').all().order_by('-id')[:5]

    top_rated_recipes = Resep.objects.annotate(
        average_rating=Avg('ratings__score'),
        total_ratings=Count('ratings')
    ).filter(
        total_ratings__gt=0  
    ).order_by('-average_rating', '-total_ratings')[:5]
    
    for recipe in top_rated_recipes:
        recipe.average_rating_rounded = round(recipe.average_rating) if recipe.average_rating else 0

    all_recipes = list(Resep.objects.all())
    random_recipes = random.sample(all_recipes, min(5, len(all_recipes))) if all_recipes else []

    context = {
        "user": request.user,
        "latest_recipes": latest_recipes,
        'top_rated_recipes': top_rated_recipes,
        'random_recipes': random_recipes
    }
    return render(request, "main.html", context)

def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    user_profiles = UserProfile.objects.select_related('user').filter(
    user__is_staff=False,
    user__is_superuser=False
).exclude(user__username="Tastify")
    AdminAccessLog.objects.create(
        admin_user=request.user,
        access_time=timezone.now(),
        action="Viewed user profiles"
    )  
    user_profiles = UserProfile.objects.select_related('user').all()
    reported_comments = Report.objects.select_related('reporter', 'comment', 'comment__user').all().order_by('-created_at')
    return render(request, 'admin_dashboard.html', {
        'user_profiles': user_profiles, 
        'reported_comments': reported_comments
    })

@login_required
@user_passes_test(is_admin)
def delete_comment(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    
    if request.method == 'POST':
        if report.comment:
            report.save_comment_info()  
            
        report.status = 'deleted'
        report.save()
        
        if report.comment:
            comment_id = report.comment.id 

            other_reports = Report.objects.filter(comment_id=comment_id, status='pending')
            for other_report in other_reports:
                other_report.save_comment_info()  
                other_report.status = 'deleted'
                other_report.save()

            report.comment.delete()
        
        messages.success(request, 'Comment has been deleted.')
    
    return redirect('main:admin_dashboard')

@login_required
@user_passes_test(is_admin)
def ignore_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    
    if request.method == 'POST':
        report.status = 'ignore'
        report.save()
        
        messages.success(request, 'Report has been ignored.')
    
    return redirect('main:admin_dashboard')

@login_required
@user_passes_test(is_admin)
def ban_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        comment_ids = list(Komentar.objects.filter(user=user).values_list('id', flat=True))
        
        # Update semua report untuk komentar user yg diban menjadi status 'banned'
        Report.objects.filter(comment_id__in=comment_ids, status='pending').update(status='banned')
        
        Komentar.objects.filter(user=user).delete()
        
        user.is_active = False
        user.save()

        try:
            profile = UserProfile.objects.get(user=user)
            profile.save()
        except UserProfile.DoesNotExist:
            pass
        
        messages.success(request, f'User {user.username} has been banned and all their comments have been removed.')
    
    return redirect('main:admin_dashboard')

@login_required
@user_passes_test(is_admin)
def clear_report_history(request):
    """Clear all processed (non-pending) reports from the system"""
    if request.method == 'POST':
        count = Report.objects.exclude(status='pending').count()
        Report.objects.exclude(status='pending').delete()
        messages.success(request, f'Successfully cleared {count} processed reports.')
    
    return redirect('main:admin_dashboard')
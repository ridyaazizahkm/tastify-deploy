from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.html import escape
from django.core.cache import cache
from .models import Komentar, Report
from .forms import KomentarForm
from resep.models import Resep
from django.contrib.auth.models import User 
import json
import bleach
import time

# Rate Limiting
RATE_LIMIT_COMMENT = {
    'max_attempts': 5,      # Maksimum 5 komentar
    'period': 60 * 60,      # Dalam periode 1 jam (dalam detik)
}

RATE_LIMIT_RATING = {
    'max_attempts': 10,     # Maksimum 10 rating
    'period': 24 * 60 * 60, # Dalam periode 1 hari (dalam detik)
}

# Untuk filter keywords offensive
OFFENSIVE_WORDS = [
    'anjing', 'babi', 'monyet', 'bangsat', 'ngentot', 'bajingan', 
    'brengsek', 'tolol', 'bodoh', 'goblok', 'idiot', 'tai', 'sialan', 
    'jelek', 'fuck', 'anying'
]

@login_required
def add_komentar(request, resep_id):
    resep = get_object_or_404(Resep, id=resep_id)

    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, 'Admin accounts cannot add comments.')
        return redirect('resep:detail_resep', id=resep_id)
    
    if request.method == 'POST':
        if check_rate_limit(request.user.id, 'comment', 
                           RATE_LIMIT_COMMENT['max_attempts'], 
                           RATE_LIMIT_COMMENT['period']):
            messages.error(
                request, 
                'Anda telah melebihi batas komentar. Silakan coba lagi nanti.',
                extra_tags='auto-dismiss'
            )
            return redirect('resep:detail_resep', id=resep_id)
        
        form = KomentarForm(request.POST)
        if form.is_valid():
            komentar = form.save(commit=False)
        
            has_offensive, offensive_word = contains_offensive_words(komentar.isi_komentar)
            if has_offensive:
                messages.error(
                    request,
                    f'Your comment contains prohibited words. Please use appropriate language.',
                    extra_tags='auto-dismiss'
                )
                return redirect('resep:detail_resep', id=resep_id)
            
            komentar.user = request.user
            komentar.resep = resep

            komentar.isi_komentar = sanitize_html(komentar.isi_komentar)
            
            komentar.save()
            messages.success(request, 'Komentar berhasil ditambahkan!')
            return redirect('resep:detail_resep', id=resep_id)
    else:
        form = KomentarForm()
    
    return render(request, 'resep/detail_resep.html', {'form': form, 'resep': resep})


@login_required
def delete_komentar(request, komentar_id):
    komentar = get_object_or_404(Komentar, id=komentar_id)

    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, 'Admin can only delete comments from the admin dashboard.')
        return redirect('resep:detail_resep', id=komentar.resep.id)
    
    if request.user == komentar.user:
        resep_id = komentar.resep.id
        komentar.delete()
        messages.success(request, 'Komentar berhasil dihapus!')
        return redirect('resep:detail_resep', id=resep_id)
    else:
        messages.error(request, 'You can only delete your own comments.')
        return redirect('resep:detail_resep', id=komentar.resep.id)

@login_required
def report_comment(request, comment_id):
    comment = get_object_or_404(Komentar, id=comment_id)

    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, 'Admin accounts cannot report comments.')
        return redirect('resep:detail_resep', id=comment.resep.id)
    
    if Report.objects.filter(reporter=request.user, comment=comment).exists():
        messages.warning(request, 'You have already reported this comment.')
        return redirect('resep:detail_resep', id=comment.resep.id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason')

        valid_reasons = [reason_code for reason_code, _ in Report.REPORT_REASONS]
        if reason not in valid_reasons:
            messages.error(request, 'Invalid report reason.')
            return redirect('resep:detail_resep', id=comment.resep.id)

        Report.objects.create(
            reporter=request.user,
            comment=comment,
            reason=reason,
            status='pending'
        )
        
        messages.success(request, 'Comment reported successfully. Our admin will review it.')
        return redirect('resep:detail_resep', id=comment.resep.id)
    
    return redirect('resep:detail_resep', id=comment.resep.id)

@login_required
def admin_moderate_comment(request, comment_id):
    """Function for admin to directly moderate comments from the detail page"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'Only admin can use this feature.')
        return redirect('resep:detail_resep', id=1)  
    
    comment = get_object_or_404(Komentar, id=comment_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        action = request.POST.get('action')
        
        valid_reasons = [reason_code for reason_code, _ in Report.REPORT_REASONS]
        if reason not in valid_reasons:
            messages.error(request, 'Invalid report reason.')
            return redirect('resep:detail_resep', id=comment.resep.id)
        
        tastify_user, created = User.objects.get_or_create(
            username='Tastify',
            defaults={
                'is_active': False,
                'email': 'system@tastify.example.com'
            }
        )

        report = Report.objects.create(
            reporter=tastify_user,
            comment=comment,
            reason=reason,
            status='pending'  
        )
    
        report.save_comment_info()
        report.save()
        
        if action == 'delete_comment':
            report.status = 'deleted'
            report.save()
            other_reports = Report.objects.filter(comment_id=comment.id, status='pending')
            for other_report in other_reports:
                other_report.save_comment_info()
                other_report.status = 'deleted'
                other_report.save()
        
            comment.delete()
            messages.success(request, 'Comment has been deleted and reported.')
            
        elif action == 'ban_user':
            user = comment.user
            user_comments = Komentar.objects.filter(user=user)
            comment_ids = list(user_comments.values_list('id', flat=True))
            report.status = 'banned'
            report.save()
            
            Report.objects.filter(comment_id__in=comment_ids, status='pending').update(status='banned')
            for user_comment in user_comments:
                if not Report.objects.filter(comment=user_comment, reporter=tastify_user).exists():
                    new_report = Report.objects.create(
                        reporter=tastify_user,
                        comment=user_comment,
                        reason=reason,
                        status='banned'
                    )
                    new_report.save_comment_info()
                    new_report.save()

            user_comments.delete()
            user.is_active = False
            user.save()
            
            messages.success(request, f'User {user.username} has been banned and all their comments have been deleted.')
        
        return redirect('resep:detail_resep', id=comment.resep.id)
    return redirect('resep:detail_resep', id=comment.resep.id)

def check_rate_limit(user_id, action_type, max_attempts, period):
    cache_key = f"rate_limit_{action_type}_{user_id}"

    rate_data = cache.get(cache_key)
    
    current_time = int(time.time())
    
    if rate_data is None:
        rate_data = {
            'count': 1,
            'reset_time': current_time + period
        }
        cache.set(cache_key, rate_data, period)
        return False
    
    if current_time > rate_data['reset_time']:
        rate_data = {
            'count': 1,
            'reset_time': current_time + period
        }
        cache.set(cache_key, rate_data, period)
        return False
    
    if rate_data['count'] >= max_attempts:
        return True
    
    rate_data['count'] += 1
    cache.set(cache_key, rate_data, period)
    return False

def contains_offensive_words(text):
    text_lower = text.lower()
    
    for word in OFFENSIVE_WORDS:
        if word in text_lower:
            return True, word
    
    return False, None

def sanitize_html(text):
    allowed_tags = ['b', 'i', 'u', 'p', 'br', 'em', 'strong']
    allowed_attributes = {}
    
    clean_text = bleach.clean(
        text,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
    return clean_text
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Bookmark
from resep.models import Resep
from authentication.models import UserProfile
from django.db.models import Q, F  

@login_required
def bookmark_list(request):
    # Pastikan profil pengguna selalu ada
    user_profile, _ = UserProfile.objects.get_or_create(
        user=request.user
    )
    
    # Ambil parameter halaman dan sorting
    page_number = request.GET.get('page', 1)
    sort_param = request.GET.get('sort', 'latest_added')
    items_per_page = request.GET.get('items_per_page', 9)

    try:
        items_per_page = int(items_per_page)
    except ValueError:
        items_per_page = 9

    # Dasar queryset bookmark
    bookmark_queryset = Bookmark.objects.filter(user=user_profile)

    # Logika sorting
    if sort_param == 'latest_added':
        # Urutkan berdasarkan waktu dibuat bookmark (default)
        bookmark_queryset = bookmark_queryset.order_by('-created_at')
    elif sort_param == 'latest_viewed':
        # Urutkan berdasarkan terakhir dilihat
        bookmark_queryset = bookmark_queryset.annotate(
            # Bookmark yang belum pernah dilihat akan diletakkan di akhir
            last_viewed_order=F('last_viewed_at')
        ).order_by(
            Q(last_viewed_at__isnull=True),  # Bookmark tanpa last_viewed_at di akhir
            '-last_viewed_order'  # Urutkan dari yang paling baru dilihat
        )
    else:
        # Default sorting
        bookmark_queryset = bookmark_queryset.order_by('-created_at')

    # Pagination
    paginator = Paginator(bookmark_queryset, items_per_page)

    try:
        page_number = int(page_number)
    except (TypeError, ValueError):
        page_number = 1

    try:
        bookmark_items = paginator.page(page_number)
    except:
        bookmark_items = paginator.page(1)

    context = {
        'bookmark_items': bookmark_items,
        'is_bookmarked': True,
        'current_sort': sort_param,
        'items_per_page': items_per_page,
        'current_page': page_number
    }

    return render(request, 'bookmark_list.html', context)

# Tambahkan method untuk mengupdate last_viewed_at saat membuka detail resep
@login_required
def bookmark_detail(request, bookmark_id):
    bookmark = get_object_or_404(Bookmark, id=bookmark_id, user=request.user.userprofile)
    
    # Update timestamp terakhir dilihat
    bookmark.update_view_timestamp()
    
    context = {
        'bookmark': bookmark,
    }
    
    return render(request, 'bookmark_list.html', context)

# Fungsi lainnya tetap sama
@login_required
@require_POST
def toggle_bookmark(request, resep_id):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        resep = get_object_or_404(Resep, id=resep_id)
        
        bookmark_exists = Bookmark.objects.filter(user=user_profile, resep=resep).exists()
        
        if bookmark_exists:
            Bookmark.objects.filter(user=user_profile, resep=resep).delete()
            is_bookmarked = False
        else:
            Bookmark.objects.create(user=user_profile, resep=resep)
            is_bookmarked = True

        return JsonResponse({
            'is_bookmarked': is_bookmarked,
            'bookmarks_count': Bookmark.objects.filter(resep=resep).count()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def check_bookmark_status(request, resep_id):
    user_profile = UserProfile.objects.get(user=request.user)
    resep = get_object_or_404(Resep, pk=resep_id)
    
    is_bookmarked = Bookmark.objects.filter(user=user_profile, resep=resep).exists()
    bookmark_count = Bookmark.objects.filter(resep=resep).count()
    
    return JsonResponse({
        'is_bookmarked': is_bookmarked,
        'bookmark_count': bookmark_count
    })
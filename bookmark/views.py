from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Bookmark
from resep.models import Resep
from authentication.models import UserProfile
from django.db.models import Q, F  
from django.utils import timezone
from django.core.cache import cache
import time
from functools import wraps

def rate_limit_bookmark(max_requests=10, window_seconds=60):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Ensure user is authenticated
            if not request.user.is_authenticated:
                return JsonResponse({'error': True, 'message': 'Authentication required'}, status=401)
                
            # Create a unique key based on user ID only (not recipe-specific)
            user_id = request.user.id
            cache_key = f"bookmark_rate_limit_{user_id}_global"
            
            # Get rate limit data from cache
            rate_data = cache.get(cache_key)
            current_time = time.time()
            
            if rate_data is None:
                # No rate limit data exists, create new
                rate_data = {
                    'count': 1,
                    'window_start': current_time
                }
                # Set cache expiry time with window_seconds + 5 second buffer
                cache.set(cache_key, rate_data, window_seconds + 5)
                return view_func(request, *args, **kwargs)
            
            # Debug info to see remaining time
            time_passed = current_time - rate_data['window_start']
            time_remaining = window_seconds - time_passed
            print(f"User {user_id}: {rate_data['count']} requests, {time_passed:.2f}s passed, {time_remaining:.2f}s remaining")
            
            # Check if window_seconds has passed
            if time_passed >= window_seconds:
                # Reset window
                print(f"Resetting rate limit for user {user_id}")
                rate_data = {
                    'count': 1,
                    'window_start': current_time
                }
                cache.set(cache_key, rate_data, window_seconds + 5)
                return view_func(request, *args, **kwargs)
            
            # Check request count
            if rate_data['count'] >= max_requests:
                # Too many requests - send user-friendly message
                retry_after = int(window_seconds - time_passed)
                
                # Get bookmark data to send with error message
                resep_id = kwargs.get('resep_id')
                resep = get_object_or_404(Resep, id=resep_id)
                user_profile = UserProfile.objects.get(user=request.user)
                is_bookmarked = Bookmark.objects.filter(user=user_profile, resep=resep).exists()
                
                print(f"Rate limit exceeded for user {user_id}. Retry after {retry_after}s")
                
                return JsonResponse({
                    'error': True,
                    'show_popup': True,
                    'is_bookmarked': is_bookmarked,
                    'bookmarks_count': Bookmark.objects.filter(resep=resep).count(),
                    'likes_count': resep.likes_count,
                    'retry_after': retry_after,
                    'resep_id': resep_id
                }, status=429)
            
            # Increment counter
            rate_data['count'] += 1
            cache.set(cache_key, rate_data, window_seconds + 5)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

@login_required(login_url='/auth/login/')
def bookmark_list(request):
    # Ensure user profile exists
    user_profile, _ = UserProfile.objects.get_or_create(
        user=request.user
    )
    
    # Get pagination and sorting parameters
    page_number = request.GET.get('page', 1)
    sort_param = request.GET.get('sort', 'newest')  # Default to newest
    items_per_page = request.GET.get('items_per_page', '9') # Default
    
    # Base bookmark queryset
    bookmark_queryset = Bookmark.objects.filter(user=user_profile)
    
    try:
        items_per_page = int(items_per_page)
        if items_per_page not in [9, 18, 24, 36]:
            items_per_page = 9
    except (TypeError, ValueError):
        items_per_page = 9
    
    # Updated sorting logic with only newest and oldest options
    if sort_param == 'newest':
        # Sort by bookmark creation date, newest first
        bookmark_queryset = bookmark_queryset.order_by('-created_at')
    elif sort_param == 'oldest':
        # Sort by bookmark creation date, oldest first
        bookmark_queryset = bookmark_queryset.order_by('created_at')
    else:
        # Default sorting if parameter is invalid
        bookmark_queryset = bookmark_queryset.order_by('-created_at')
    
    # Create paginator after sorting
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

# Update last_viewed_at when opening recipe details
@login_required
def bookmark_detail(request, bookmark_id):
    bookmark = get_object_or_404(Bookmark, id=bookmark_id, user=request.user.userprofile)
    
    # Update timestamp for last viewed
    bookmark.update_view_timestamp()
    
    context = {
        'bookmark': bookmark,
    }
    
    return render(request, 'bookmark_list.html', context)

# Other functions remain the same
@login_required
@require_POST
@rate_limit_bookmark(max_requests=10, window_seconds=60)
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

        # Update likes count
        resep.update_likes_count()

        return JsonResponse({
            'is_bookmarked': is_bookmarked,
            'bookmarks_count': Bookmark.objects.filter(resep=resep).count(),
            'likes_count': resep.likes_count 
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def check_bookmark_status(request, resep_id):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    resep = get_object_or_404(Resep, pk=resep_id)
    
    is_bookmarked = Bookmark.objects.filter(user=user_profile, resep=resep).exists()
    bookmark_count = Bookmark.objects.filter(resep=resep).count()
    
    return JsonResponse({
        'is_bookmarked': is_bookmarked,
        'bookmark_count': bookmark_count
    })

@login_required
def reset_bookmark_rate_limit(request):
    """Endpoint to manually reset bookmark rate limit"""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)
    
    # Delete the global rate limit key for this user
    user_id = request.user.id
    cache_key = f"bookmark_rate_limit_{user_id}_global"

    deleted = cache.delete(cache_key)
    
    if deleted:
        return JsonResponse({
            'status': 'success',
            'message': 'Rate limit has been reset successfully'
        })
    else:
        return JsonResponse({
            'status': 'warning',
            'message': 'No active rate limit found to reset'
        })
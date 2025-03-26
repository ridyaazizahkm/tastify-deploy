# bookmark/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Recipe, Bookmark

@login_required
def bookmark_list(request):
    bookmarks = Bookmark.objects.filter(user=request.user).order_by('-bookmarked_at')
    return render(request, 'bookmark/bookmark_list.html', {'bookmarks': bookmarks})

@login_required
def add_bookmark(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    
    # Cek apakah sudah di-bookmark
    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user, 
        recipe=recipe
    )
    
    return redirect('bookmark_list')

@login_required
def remove_bookmark(request, recipe_id):
    bookmark = get_object_or_404(Bookmark, user=request.user, recipe_id=recipe_id)
    bookmark.delete()
    return redirect('bookmark_list')
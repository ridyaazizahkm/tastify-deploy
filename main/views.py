from django.shortcuts import render
from resep.models import Resep
from rating.models import Rating
from django.contrib.auth.decorators import login_required, user_passes_test
from authentication.models import UserProfile
from django.db.models import Avg, Count, F

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

    context = {
        "user": request.user,
        "latest_recipes": latest_recipes,
        'top_rated_recipes': top_rated_recipes
    }
    return render(request, "main.html", context)

def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    user_profiles = UserProfile.objects.select_related('user').all()
    return render(request, 'admin_dashboard.html', {'user_profiles': user_profiles})

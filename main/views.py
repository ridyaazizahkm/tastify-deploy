from django.shortcuts import render
from resep.models import Resep
from rating.models import Rating
from authentication.models import AdminAccessLog
from django.contrib.auth.decorators import login_required, user_passes_test
from authentication.models import UserProfile
from django.db.models import Avg, Count, F
import random
from django.utils import timezone

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
    return render(request, 'admin_dashboard.html', {'user_profiles': user_profiles})   
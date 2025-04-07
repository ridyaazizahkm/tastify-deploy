from django.shortcuts import render
from resep.models import Resep
from django.contrib.auth.decorators import login_required, user_passes_test
from authentication.models import UserProfile

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
@login_required
def admin_dashboard(request):
    user_profiles = UserProfile.objects.select_related('user').all()
    return render(request, 'admin_dashboard.html', {'user_profiles': user_profiles})

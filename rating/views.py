from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Rating
from resep.models import Resep

@login_required
def add_rating(request, resep_id):
    if request.method == "POST":
        resep = get_object_or_404(Resep, id=resep_id)
        score = int(request.POST.get('score', 0))

        if 1 <= score <= 5:
            rating, created = Rating.objects.update_or_create(
                user=request.user,
                resep=resep,
                defaults={'score': score}
            )
            return JsonResponse({
                "average_rating": resep.average_rating(),
                "total_ratings": resep.total_ratings(),
                "new_rating": rating.score
            })
        return JsonResponse({"error": "Invalid rating"}, status=400)

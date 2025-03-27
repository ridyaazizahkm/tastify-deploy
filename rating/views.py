from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone  
from django.db.models import Avg 

from komentar.views import RATE_LIMIT_RATING, check_rate_limit
from rating.models import Rating
from resep.models import Resep

@login_required
def add_rating(request, resep_id):
    resep = get_object_or_404(Resep, id=resep_id)
    
    if request.method == 'POST':
        # Cek rate limiting
        if check_rate_limit(request.user.id, 'rating', 
                           RATE_LIMIT_RATING['max_attempts'], 
                           RATE_LIMIT_RATING['period']):
            return JsonResponse({
                'error': 'Anda telah melebihi batas rating. Silakan coba lagi besok.'
            })
        
        try:
            score = int(request.POST.get('score', 0))
        
            existing_rating = Rating.objects.filter(user=request.user, resep=resep).first()
            
            if existing_rating:
                existing_rating.score = score
                existing_rating.updated_at = timezone.now()
                existing_rating.save()
                message = 'Rating berhasil diperbarui!'
            else:
                # Buat rating baru
                Rating.objects.create(user=request.user, resep=resep, score=score)
                message = 'Rating berhasil ditambahkan!'
            
            # Hitung rata-rata rating dan total ratings
            average_rating = Rating.objects.filter(resep=resep).aggregate(avg_score=Avg('score'))['avg_score'] or 0
            total_ratings = Rating.objects.filter(resep=resep).count()
            
            return JsonResponse({
                'success': True,
                'message': message,
                'average_rating': float(average_rating),
                'total_ratings': total_ratings
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)})

    return JsonResponse({'error': 'Metode tidak valid'})
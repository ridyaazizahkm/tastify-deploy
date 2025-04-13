from django.db import models
from django.contrib.auth.models import User
from resep.models import Resep
from django.db.models import Avg, Count
from django.db.models import Avg
class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resep = models.ForeignKey(Resep, on_delete=models.CASCADE, related_name='ratings')
    score = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'resep')  # 1 user 1 rating per resep

    def __str__(self):
        return f"{self.user.username} - {self.resep.judul} - {self.score}"
    
    @classmethod
    def average_rating(cls, resep):
        return round(cls.objects.filter(resep=resep).aggregate(avg_rating=Avg('score'))['avg_rating'] or 0, 2)

    @classmethod
    def total_reviews(cls, resep):
        return cls.objects.filter(resep=resep).count()

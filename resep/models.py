from django.db import models
from authentication.models import UserProfile
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models import Avg

class Kategori(models.Model):
    nama = models.CharField(max_length=100)

    def __str__(self):
        return self.nama


class Bahan(models.Model):
    nama = models.CharField(max_length=100)

    def __str__(self):
        return self.nama


class CookingMethod(models.Model):
    nama = models.CharField(max_length=100)

    def __str__(self):
        return self.nama


class Resep(models.Model):
    judul = models.CharField(max_length=100)
    deskripsi = models.TextField()
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    alat = models.TextField()
    bahan = models.TextField()
    langkah = models.TextField()
    kategori = models.ForeignKey(Kategori, on_delete=models.CASCADE)
    metode_masak = models.ForeignKey(CookingMethod, on_delete=models.CASCADE)
    bahan_utama = models.ForeignKey(Bahan, on_delete=models.CASCADE, related_name='resep_bahan_utama')
    url_foto = models.URLField()
    durasi = models.IntegerField()
    porsi = models.IntegerField()
    likes_count = models.IntegerField(default=0)

    def update_likes_count(self):
        from bookmark.models import Bookmark
        self.likes_count = Bookmark.objects.filter(resep=self).count()
        self.save(update_fields=['likes_count'])

    def __str__(self):
        return self.judul
    
    def average_rating(self):
        avg_nilai = self.ratings.aggregate(Avg('score'))
        return avg_nilai.get('score__avg', 0) or 0.0

    def total_ratings(self):
        return self.ratings.count()
    

class RecipeReport(models.Model):
    REPORT_REASONS = [
        ('inappropriate', 'Inappropriate content'),
        ('copyright', 'Copyright violation'),
        ('offensive', 'Offensive content'),
        ('spam', 'Spam or advertisement'),
        ('harmful', 'Harmful or dangerous content'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('deleted', 'Deleted'), 
        ('banned', 'Banned User'),  
        ('ignore', 'Ignored'),  
    ]
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_recipes')
    recipe = models.ForeignKey(Resep, on_delete=models.SET_NULL, related_name='reports', null=True)
    recipe_info = models.JSONField(null=True, blank=True)  # Store recipe info when deleted
    reason = models.CharField(max_length=50, choices=REPORT_REASONS)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    def __str__(self):
        if self.recipe:
            return f"Report by {self.reporter.username} on {self.recipe.user.user.username}'s recipe"
        elif self.recipe_info:
            return f"Report by {self.reporter.username} on {self.recipe_info.get('author')}'s recipe"
        else:
            return f"Report by {self.reporter.username} on deleted recipe"
            
    def save_recipe_info(self):
        if self.recipe:
            self.recipe_info = {
                'title': self.recipe.judul,
                'author': self.recipe.user.user.username,
                'author_id': self.recipe.user.user.id,
                'description': self.recipe.deskripsi,
                'category': self.recipe.kategori.nama,
                'cooking_method': self.recipe.metode_masak.nama,
                'main_ingredient': self.recipe.bahan_utama.nama,
                'created_at': self.recipe.created_at.isoformat() if hasattr(self.recipe, 'created_at') else None
            }
            self.save(update_fields=['recipe_info'])
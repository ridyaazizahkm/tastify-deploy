from django.db import models
from django.contrib.auth.models import User
from resep.models import Resep

class Komentar(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='komentar')
    resep = models.ForeignKey(Resep, on_delete=models.CASCADE, related_name='komentar')
    isi_komentar = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.resep.judul}"
    
    class Meta:
        ordering = ['-created_at']
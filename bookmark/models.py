from django.db import models
from django.utils import timezone
from authentication.models import UserProfile
from resep.models import Resep

class Bookmark(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='bookmarks')
    resep = models.ForeignKey(Resep, on_delete=models.CASCADE, related_name='bookmarked')
    created_at = models.DateTimeField(default=timezone.now)
    last_viewed_at = models.DateTimeField(null=True, blank=True)

    def update_view_timestamp(self):
        """
        Update timestamp terakhir dilihat
        """
        self.last_viewed_at = timezone.now()
        self.save(update_fields=['last_viewed_at'])

    class Meta:
        unique_together = ('user', 'resep')  # Mencegah bookmark duplikat
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.user.username} - {self.resep.judul}"
from django.db import models
from django.contrib.auth.models import User
from resep.models import Resep
import json

class Komentar(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='komentar')
    resep = models.ForeignKey(Resep, on_delete=models.CASCADE, related_name='komentar')
    isi_komentar = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.resep.judul}"
    
    class Meta:
        ordering = ['-created_at']

class Report(models.Model):
    REPORT_REASONS = [
        ('hate_speech', 'Hate speech'),
        ('harassment', 'Harassment or bullying'),
        ('threats', 'Threats of violence or physical harm'),
        ('offensive', 'Offensive or abusive language'),
        ('spam', 'Spam'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('deleted', 'Deleted'), 
        ('banned', 'Banned'),  
        ('ignore', 'Ignored'),  
    ]
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_comments')
    comment = models.ForeignKey(Komentar, on_delete=models.SET_NULL, related_name='reports', null=True)
    comment_info = models.JSONField(null=True, blank=True)  
    reason = models.CharField(max_length=50, choices=REPORT_REASONS)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    def __str__(self):
        if self.comment:
            return f"Report by {self.reporter.username} on {self.comment.user.username}'s comment"
        elif self.comment_info:
            return f"Report by {self.reporter.username} on {self.comment_info.get('username')}'s comment"
        else:
            return f"Report by {self.reporter.username} on deleted comment"
            
    def save_comment_info(self):
        if self.comment:
            self.comment_info = {
                'username': self.comment.user.username,
                'user_id': self.comment.user.id,
                'content': self.comment.isi_komentar,
                'created_at': self.comment.created_at.isoformat(),
                'resep_id': self.comment.resep.id
            }
            self.save(update_fields=['comment_info'])
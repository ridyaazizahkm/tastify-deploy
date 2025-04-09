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
        ('approved', 'Approved'),
        ('declined', 'Declined'),
    ]
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_comments')
    comment = models.ForeignKey(Komentar, on_delete=models.CASCADE, related_name='reports')
    reason = models.CharField(max_length=50, choices=REPORT_REASONS)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return f"Report by {self.reporter.username} on {self.comment.user.username}'s comment"
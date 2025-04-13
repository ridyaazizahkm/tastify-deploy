from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
import os
from django.conf import settings
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    encrypted_email = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Enkripsi email saat menyimpan profile
        if self.user.email and not self.encrypted_email:
            encryptor = Encryption()
            self.encrypted_email = encryptor.encrypt(self.user.email)
        super().save(*args, **kwargs)
    
    def get_email(self):
        # Metode untuk mendapatkan email asli
        if self.encrypted_email:
            encryptor = Encryption()
            return encryptor.decrypt(self.encrypted_email)
        return self.user.email
    
    def __str__(self):
        return f'{self.user.username} Profile'
    
class Encryption:
    def __init__(self):
        self.key = settings.ENCRYPTION_KEY
        self.cipher = Fernet(self.key)
    
    def encrypt(self, text):
        if text:
            return self.cipher.encrypt(text.encode()).decode()
        return None
    
    def decrypt(self, encrypted_text):
        if encrypted_text:
            return self.cipher.decrypt(encrypted_text.encode()).decode()
        return None
    
class AdminAccessLog(models.Model):
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE)
    access_time = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.admin_user.username} - {self.action} at {self.access_time}"

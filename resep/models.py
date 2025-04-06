from django.db import models
from authentication.models import UserProfile
from django.dispatch import receiver

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
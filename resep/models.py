from django.db import models
from authentication.models import UserProfile

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

    def __str__(self):
        return self.judul
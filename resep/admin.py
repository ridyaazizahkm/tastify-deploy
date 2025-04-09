from django.contrib import admin

# Register your models here.
from .models import Resep, Kategori, Bahan, CookingMethod

admin.site.register(Resep)
admin.site.register(Kategori)
admin.site.register(Bahan)
admin.site.register(CookingMethod)



from django.db import migrations

def create_initial_data(apps, schema_editor):
    Kategori = apps.get_model('resep', 'Kategori')
    Bahan = apps.get_model('resep', 'Bahan')
    CookingMethod = apps.get_model('resep', 'CookingMethod')

    Kategori.objects.create(nama='Dessert')
    Kategori.objects.create(nama='Healthy Food')
    Kategori.objects.create(nama='Fast Food')
    Kategori.objects.create(nama='Beverage')
    Kategori.objects.create(nama='Traditional Food')

    Bahan.objects.create(nama='Roti')
    Bahan.objects.create(nama='Buah & Sayur')
    Bahan.objects.create(nama='Daging')
    Bahan.objects.create(nama='Coklat')
    Bahan.objects.create(nama='Seafood')

    CookingMethod.objects.create(nama='Fried')
    CookingMethod.objects.create(nama='Boiled')
    CookingMethod.objects.create(nama='Steamed')
    CookingMethod.objects.create(nama='Baked')
    CookingMethod.objects.create(nama='Blender')

def reverse_initial_data(apps, schema_editor):
    Kategori = apps.get_model('resep', 'Kategori')
    Bahan = apps.get_model('resep', 'Bahan')
    CookingMethod = apps.get_model('resep', 'CookingMethod')

    Kategori.objects.all().delete()
    Bahan.objects.all().delete()
    CookingMethod.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('resep', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_data, reverse_initial_data),
    ]

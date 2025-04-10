import csv
import os
from django.db import migrations
from django.core.exceptions import ImproperlyConfigured

def load_csv_data(apps, schema_editor):
    Resep = apps.get_model('resep', 'Resep')
    Kategori = apps.get_model('resep', 'Kategori')
    Bahan = apps.get_model('resep', 'Bahan')
    CookingMethod = apps.get_model('resep', 'CookingMethod')
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('authentication', 'UserProfile')

    default_username = 'Tastify'
    default_user, created = User.objects.get_or_create(
        username=default_username,
        defaults={
            'is_staff': True,
            'is_active': True,
            'email': 'tastify@example.com'
        }
    )

    if created:
        print(f"Created default user: {default_username}")
        from django.contrib.auth.hashers import make_password
        default_user.password = make_password('tastify123')  # Set a default password
        default_user.save()

    default_profile, profile_created = UserProfile.objects.get_or_create(
        user=default_user,
        defaults={'encrypted_email': 'tastify@example.com'}
    )
    if profile_created:
        print(f"Created UserProfile for default user: {default_username}")

    possible_paths = [
        os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'DATABASE_TASTIFY_RESEP_Sheet1.csv'),
        os.path.join(os.path.dirname(__file__), 'DATABASE_TASTIFY_RESEP_Sheet1.csv'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fixtures', 'DATABASE_TASTIFY_RESEP_Sheet1.csv'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'fixtures', 'DATABASE_TASTIFY_RESEP_Sheet1.csv'),
    ]

    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            break

    if not csv_path:
        raise ImproperlyConfigured(
            "CSV file 'DATABASE_TASTIFY_RESEP_Sheet1.csv' not found. Please place it in one of the following locations:\n" +
            "\n".join(possible_paths)
        )

    fixtures_dir = os.path.join(os.path.dirname(__file__), '..', 'fixtures')
    if not os.path.exists(fixtures_dir):
        try:
            os.makedirs(fixtures_dir)
            print(f"Created fixtures directory at {fixtures_dir}")
        except OSError:
            print(f"Could not create fixtures directory at {fixtures_dir}")

    recipes_to_create = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            kategori_obj = Kategori.objects.filter(nama=row['Jenis Hidangan']).first()
            if not kategori_obj:
                kategori_obj = Kategori.objects.create(nama=row['Jenis Hidangan'])

            metode_obj = CookingMethod.objects.filter(nama=row['Metode memasak']).first()
            if not metode_obj:
                metode_obj = CookingMethod.objects.create(nama=row['Metode memasak'])

            bahan_utama_obj = Bahan.objects.filter(nama=row['Bahan Utama']).first()
            if not bahan_utama_obj:
                bahan_utama_obj = Bahan.objects.create(nama=row['Bahan Utama'])

            try:
                user_obj = UserProfile.objects.get(user__username=row['User'])
            except UserProfile.DoesNotExist:
                print(f"User with username {row['User']} not found. Using default user '{default_username}' instead.")
                user_obj = default_profile

            judul = row['Nama Resep'] or "Untitled Recipe"
            deskripsi = row['Deskripsi'] or "No description"
            alat = row['Alat-alat'] or "No tools specified"
            bahan = row['Bahan-bahan'] or "No ingredients specified"
            langkah = row['Cara Membuat'] or "No steps provided"
            url_foto = row['Foto'] or ""
            durasi = int(row['Waktu Memasak']) if row['Waktu Memasak'] else 0
            porsi = int(row['Porsi']) if row['Porsi'] else 1

            resep = Resep(
                judul=judul,
                deskripsi=deskripsi,
                user=user_obj,
                alat=alat,
                bahan=bahan,
                langkah=langkah,
                kategori=kategori_obj,
                metode_masak=metode_obj,
                bahan_utama=bahan_utama_obj,
                url_foto=url_foto,
                durasi=durasi,
                porsi=porsi
            )
            recipes_to_create.append(resep)

    Resep.objects.bulk_create(recipes_to_create)

def unload_csv_data(apps, schema_editor):
    Resep = apps.get_model('resep', 'Resep')

    possible_paths = [
        os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'DATABASE_TASTIFY_RESEP_Sheet1.csv'),
        os.path.join(os.path.dirname(__file__), 'DATABASE_TASTIFY_RESEP_Sheet1.csv'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fixtures', 'DATABASE_TASTIFY_RESEP_Sheet1.csv'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'fixtures', 'DATABASE_TASTIFY_RESEP_Sheet1.csv'),
    ]

    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            break

    if not csv_path:
        print("Warning: CSV file not found for reverse migration. No data will be removed.")
        return

    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        juduls = [row['judul'] for row in reader]
    Resep.objects.filter(judul__in=juduls).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('resep', '0001_initial'),
        ('resep', '0002_initial_data'),
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_csv_data, reverse_code=unload_csv_data),
    ]

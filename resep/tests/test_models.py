import pytest
from resep.models import Resep, Kategori, CookingMethod, Bahan
from authentication.models import UserProfile
from django.contrib.auth.models import User
from bookmark.models import Bookmark
from django.db.models import Avg

@pytest.fixture
def user():
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpassword'
    )
    return user

@pytest.fixture
def user_profile(user):
    profile = UserProfile.objects.create(
        user=user,
        bio='Test bio'
    )
    return profile

@pytest.fixture
def kategori():
    return Kategori.objects.create(nama='Healthy Food')

@pytest.fixture
def metode_masak():
    return CookingMethod.objects.create(nama='Baked')

@pytest.fixture
def bahan_utama():
    return Bahan.objects.create(nama='Roti')

@pytest.fixture
def resep(user_profile, kategori, metode_masak, bahan_utama):
    return Resep.objects.create(
        judul='Test Recipe',
        deskripsi='This is a test recipe',
        user=user_profile,
        alat='Test tools',
        bahan='Test ingredients',
        langkah='Test steps',
        kategori=kategori,
        metode_masak=metode_masak,
        bahan_utama=bahan_utama,
        url_foto='https://example.com/image.jpg',
        durasi=30,
        porsi=4
    )

@pytest.mark.django_db
class TestKategori:
    def test_kategori_creation(self, kategori):
        assert kategori.nama == 'Healthy Food'

    def test_kategori_str(self, kategori):
        assert str(kategori) == 'Healthy Food'

@pytest.mark.django_db
class TestCookingMethod:
    def test_cooking_method_creation(self, metode_masak):
        assert metode_masak.nama == 'Baked'

    def test_cooking_method_str(self, metode_masak):
        assert str(metode_masak) == 'Baked'

@pytest.mark.django_db
class TestBahan:
    def test_bahan_creation(self, bahan_utama):
        assert bahan_utama.nama == 'Roti'

    def test_bahan_str(self, bahan_utama):
        assert str(bahan_utama) == 'Roti'

@pytest.mark.django_db
class TestResep:
    def test_resep_creation(self, resep):
        assert resep.judul == 'Test Recipe'
        assert resep.deskripsi == 'This is a test recipe'
        assert resep.durasi == 30
        assert resep.porsi == 4

    def test_resep_str(self, resep):
        assert str(resep) == 'Test Recipe'

    def test_update_likes_count(self, resep, user_profile):
        assert resep.likes_count == 0

        Bookmark.objects.create(user=user_profile, resep=resep)

        resep.update_likes_count()

        assert resep.likes_count == 1

    def test_average_rating_without_ratings(self, resep):
        assert resep.average_rating() == 0.0

    def test_total_ratings_without_ratings(self, resep):
        assert resep.total_ratings() == 0

    def test_average_rating_with_ratings(self, resep):
        try:
            from rating.models import Rating
            user = resep.user.user

            Rating.objects.filter(user=user, resep=resep).delete()

            Rating.objects.create(user=user, resep=resep, score=4)

            user2 = User.objects.create_user(username="testuser2", email="test2@example.com", password="password")
            Rating.objects.create(user=user2, resep=resep, score=5)

            assert resep.average_rating() == 4.5
        except ImportError:
            pytest.skip("Rating model not available")

    def test_total_ratings_with_ratings(self, resep):
        try:
            from rating.models import Rating
            user = resep.user.user

            Rating.objects.filter(user=user, resep=resep).delete()

            Rating.objects.create(user=user, resep=resep, score=4)

            user2 = User.objects.create_user(username="testuser3", email="test3@example.com", password="password")
            Rating.objects.create(user=user2, resep=resep, score=5)

            assert resep.total_ratings() == 2
        except ImportError:
            pytest.skip("Rating model not available")
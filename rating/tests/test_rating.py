import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache
from unittest.mock import patch, MagicMock

from rating.views import add_rating
from rating.models import Rating
from resep.models import Resep
from authentication.models import UserProfile
from komentar.views import check_rate_limit

pytestmark = pytest.mark.django_db

@pytest.fixture
def setup_users():
    user = User.objects.create_user(
        username='testuser', 
        email='testuser@example.com',
        password='testpassword123'
    )

    user_profile = UserProfile.objects.create(
        user=user,
        bio='Test Bio'
    )

    other_user = User.objects.create_user(
        username='otheruser', 
        email='otheruser@example.com',
        password='testpassword123'
    )

    other_user_profile = UserProfile.objects.create(
        user=other_user,
        bio='Other Bio'
    )

    admin_user = User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='adminpassword123',
        is_staff=True
    )

    admin_user_profile = UserProfile.objects.create(
        user=admin_user,
        bio='Admin Bio'
    )
    
    return {
        'regular_user': user, 
        'regular_profile': user_profile,
        'other_user': other_user, 
        'other_profile': other_user_profile,
        'admin_user': admin_user,
        'admin_profile': admin_user_profile
    }

@pytest.fixture
def setup_resep(setup_users):
    from resep.models import Kategori, Bahan, CookingMethod
    
    kategori = Kategori.objects.create(nama='Test Category')
    bahan = Bahan.objects.create(nama='Test Ingredient')
    method = CookingMethod.objects.create(nama='Test Method')
    
    resep = Resep.objects.create(
        judul='Test Recipe',
        deskripsi='Test Description',
        user=setup_users['regular_profile'], 
        bahan='Test Ingredients',
        langkah='Test Steps',
        kategori=kategori,
        metode_masak=method,
        bahan_utama=bahan,
        url_foto='http://example.com/test.jpg',
        durasi=30,
        porsi=4
    )
    
    return resep

@pytest.fixture
def setup_rating(setup_users, setup_resep):
    rating = Rating.objects.create(
        user=setup_users['regular_user'],  
        resep=setup_resep,
        score=4
    )
    
    return rating

@pytest.fixture
def client():
    return Client()


class TestAddRating:
    def test_add_rating_success(self, setup_users, setup_resep, client):
        client.login(username='testuser', password='testpassword123')
        
        data = {
            'score': 5
        }
        
        response = client.post(
            reverse('rating:add_rating', args=[setup_resep.id]),
            data=data
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['success'] is True
        assert response_data['message'] == 'Rating berhasil ditambahkan!'
        
        rating = Rating.objects.get(user=setup_users['regular_user'], resep=setup_resep)
        assert rating.score == 5
    
    def test_update_existing_rating(self, setup_users, setup_rating, setup_resep, client):
        client.login(username='testuser', password='testpassword123')
        data = {
            'score': 2
        }
        
        response = client.post(
            reverse('rating:add_rating', args=[setup_resep.id]),
            data=data
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['success'] is True
        assert response_data['message'] == 'Rating berhasil diperbarui!'
        
        rating = Rating.objects.get(user=setup_users['regular_user'], resep=setup_resep)
        assert rating.score == 2
    
    def test_add_rating_admin_blocked(self, setup_users, setup_resep, client):
        client.login(username='adminuser', password='adminpassword123')
        
        data = {
            'score': 5
        }
        
        response = client.post(
            reverse('rating:add_rating', args=[setup_resep.id]),
            data=data
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert 'error' in response_data
        assert 'Admin accounts cannot add ratings' in response_data['error']
        
        assert not Rating.objects.filter(
            user=setup_users['admin_user'],
            resep=setup_resep
        ).exists()
    
    def test_add_rating_invalid_method(self, setup_users, setup_resep, client):
        client.login(username='testuser', password='testpassword123')
        
        response = client.get(
            reverse('rating:add_rating', args=[setup_resep.id])
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert 'error' in response_data
        assert 'Metode tidak valid' in response_data['error']
    
    def test_add_rating_invalid_score(self, setup_users, setup_resep, client):
        client.login(username='testuser', password='testpassword123')
        
        data = {
            'score': 'not_a_number'
        }
        
        response = client.post(
            reverse('rating:add_rating', args=[setup_resep.id]),
            data=data
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert 'error' in response_data
        assert "invalid literal for int()" in response_data['error']
    
    @patch('rating.views.check_rate_limit')
    def test_add_rating_rate_limit(self, mock_rate_limit, setup_users, setup_resep, client):
        mock_rate_limit.return_value = True
        client.login(username='testuser', password='testpassword123')
        
        data = {
            'score': 3
        }
        
        response = client.post(
            reverse('rating:add_rating', args=[setup_resep.id]),
            data=data
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert 'error' in response_data
        assert 'melebihi batas rating' in response_data['error']
    
    def test_add_rating_unauthenticated(self, setup_resep, client):
        data = {
            'score': 5
        }
        
        response = client.post(
            reverse('rating:add_rating', args=[setup_resep.id]),
            data=data
        )
        
        assert response.status_code in [302, 403]


class TestRatingCalculations:
    def test_average_rating_calculation(self, setup_users, setup_rating, setup_resep, client):
        Rating.objects.create(
            user=setup_users['other_user'],
            resep=setup_resep,
            score=2
        )
        
        client.login(username='testuser', password='testpassword123')
        
        data = {
            'score': 5
        }
        
        response = client.post(
            reverse('rating:add_rating', args=[setup_resep.id]),
            data=data
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data['average_rating'] == 3.5
        assert response_data['total_ratings'] == 2
    
    def test_model_rating_methods(self, setup_users, setup_resep):
        Rating.objects.create(
            user=setup_users['regular_user'],
            resep=setup_resep,
            score=5
        )
        
        Rating.objects.create(
            user=setup_users['other_user'],
            resep=setup_resep,
            score=3
        )
        
        avg_rating = Rating.average_rating(setup_resep)
        assert avg_rating == 4.0
        
        total = Rating.total_reviews(setup_resep)
        assert total == 2
    
    def test_no_ratings(self, setup_resep):
        Rating.objects.filter(resep=setup_resep).delete()
        
        avg_rating = Rating.average_rating(setup_resep)
        assert avg_rating == 0
        
        total = Rating.total_reviews(setup_resep)
        assert total == 0
    
    def test_resep_average_rating_method(self, setup_users, setup_resep):
        Rating.objects.create(
            user=setup_users['regular_user'],
            resep=setup_resep,
            score=5
        )
        
        Rating.objects.create(
            user=setup_users['other_user'],
            resep=setup_resep,
            score=3
        )
        
        avg = setup_resep.average_rating()
        assert float(avg) == 4.0
        
    def test_resep_total_ratings_method(self, setup_users, setup_resep):
        Rating.objects.create(
            user=setup_users['regular_user'],
            resep=setup_resep,
            score=4
        )
        
        Rating.objects.create(
            user=setup_users['other_user'],
            resep=setup_resep,
            score=2
        )
        
        total = setup_resep.total_ratings()
        assert total == 2


class TestRatingConstraints:    
    def test_unique_user_resep_constraint(self, setup_users, setup_resep):
        Rating.objects.create(
            user=setup_users['regular_user'],
            resep=setup_resep,
            score=4
        )
        
        with pytest.raises(Exception) as excinfo:
            Rating.objects.create(
                user=setup_users['regular_user'],
                resep=setup_resep,
                score=5
            )
        
        assert "UNIQUE constraint" in str(excinfo.value) or "duplicate key" in str(excinfo.value)

class TestRatingIntegration:
    def test_rating_cascade_on_resep_delete(self, setup_users, setup_resep, setup_rating):
        assert Rating.objects.filter(
            user=setup_users['regular_user'],
            resep=setup_resep
        ).exists()
        
        setup_resep.delete()
        
        assert not Rating.objects.filter(
            user=setup_users['regular_user'],
            resep_id=setup_resep.id
        ).exists()
    
    def test_rating_cascade_on_user_delete(self, setup_users, setup_resep, setup_rating):
        assert Rating.objects.filter(
            user=setup_users['regular_user'],
            resep=setup_resep
        ).exists()
        
        setup_users['regular_user'].delete()
        
        assert not Rating.objects.filter(
            user_id=setup_users['regular_user'].id,
            resep=setup_resep
        ).exists()
    
    def test_resep_with_multiple_users_ratings(self, setup_users, setup_resep):
        Rating.objects.create(
            user=setup_users['regular_user'],
            resep=setup_resep,
            score=5
        )
        
        Rating.objects.create(
            user=setup_users['other_user'],
            resep=setup_resep,
            score=2
        )
        
        assert Rating.objects.filter(resep=setup_resep).count() == 2
        
        assert Rating.average_rating(setup_resep) == 3.5
    
    def test_user_with_multiple_resep_ratings(self, setup_users, setup_resep):
        from resep.models import Kategori, Bahan, CookingMethod
        
        kategori = Kategori.objects.create(nama='Another Category')
        bahan = Bahan.objects.create(nama='Another Ingredient')
        method = CookingMethod.objects.create(nama='Another Method')
        
        another_resep = Resep.objects.create(
            judul='Another Recipe',
            deskripsi='Another Description',
            user=setup_users['other_profile'],
            alat='Another Tools',
            bahan='Another Ingredients',
            langkah='Another Steps',
            kategori=kategori,
            metode_masak=method,
            bahan_utama=bahan,
            url_foto='http://example.com/another.jpg',
            durasi=45,
            porsi=6
        )
        
        Rating.objects.create(
            user=setup_users['regular_user'],
            resep=setup_resep,
            score=5
        )
        
        Rating.objects.create(
            user=setup_users['regular_user'],
            resep=another_resep,
            score=3
        )
        
        assert Rating.objects.filter(user=setup_users['regular_user']).count() == 2
        
        rating1 = Rating.objects.get(user=setup_users['regular_user'], resep=setup_resep)
        rating2 = Rating.objects.get(user=setup_users['regular_user'], resep=another_resep)
        assert rating1.score == 5
        assert rating2.score == 3

import pytest
from django.test import RequestFactory, Client
from django.urls import reverse
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.cache import cache
from unittest.mock import patch, MagicMock

from komentar.views import (
    add_komentar, delete_komentar, report_comment, admin_moderate_comment,
    check_rate_limit, contains_offensive_words, sanitize_html
)
from komentar.models import Komentar, Report
from komentar.forms import KomentarForm
from resep.models import Resep
from authentication.models import UserProfile

# Mark all tests in this file to have database access
pytestmark = pytest.mark.django_db

@pytest.fixture
def setup_users():
    # Create regular user
    user = User.objects.create_user(
        username='testuser', 
        email='testuser@example.com',
        password='testpassword123'
    )
    
    # Create UserProfile for the user
    user_profile = UserProfile.objects.create(
        user=user,
        bio='Test Bio'
    )
    
    # Create another user for interaction tests
    other_user = User.objects.create_user(
        username='otheruser', 
        email='otheruser@example.com',
        password='testpassword123'
    )
    
    # Create UserProfile for the other user
    other_user_profile = UserProfile.objects.create(
        user=other_user,
        bio='Other Bio'
    )
    
    # Create admin user
    admin_user = User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='adminpassword123',
        is_staff=True
    )
    
    # Create UserProfile for the admin user
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
    # Since Resep has relationships to several models, we need to mock or create test instances
    from resep.models import Kategori, Bahan, CookingMethod
    
    kategori = Kategori.objects.create(nama='Test Category')
    bahan = Bahan.objects.create(nama='Test Ingredient')
    method = CookingMethod.objects.create(nama='Test Method')
    
    # Create a test recipe
    resep = Resep.objects.create(
        judul='Test Recipe',
        deskripsi='Test Description',
        user=setup_users['regular_profile'],  # Using UserProfile instead of User
        alat='Test Tools',
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
def setup_komentar(setup_users, setup_resep):
    # Create a test comment - Note: User is used for Komentar, not UserProfile
    komentar = Komentar.objects.create(
        user=setup_users['regular_user'],  # Use User, not UserProfile
        resep=setup_resep,
        isi_komentar='This is a test comment'
    )
    
    return komentar

@pytest.fixture
def client():
    return Client()

def add_session_to_request(request):
    """Helper function to add session to request"""
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()
    
    # Set up messages
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    
    return request


class TestAddKomentar:    
    def test_add_komentar_get(self, setup_users, setup_resep, client):
        """Test GET request for add_komentar view"""
        client.login(username='testuser', password='testpassword123')
        response = client.get(reverse('resep:detail_resep', args=[setup_resep.id]))
        
        assert response.status_code == 200

    def test_add_komentar_success(self, setup_users, setup_resep, client):
        """Test successful comment submission"""
        client.login(username='testuser', password='testpassword123')
        
        data = {
            'isi_komentar': 'This is a new comment for testing'
        }
        
        response = client.post(
            reverse('komentar:add_komentar', args=[setup_resep.id]),
            data=data,
            follow=True
        )
        
        assert response.status_code == 200
        assert Komentar.objects.filter(
            user=setup_users['regular_user'], 
            resep=setup_resep,
            isi_komentar='This is a new comment for testing'
        ).exists()

        messages = list(response.context.get('messages', []))
        assert any('Komentar berhasil ditambahkan' in str(message) for message in messages)
    
    def test_add_komentar_with_offensive_words(self, setup_users, setup_resep, client):
        client.login(username='testuser', password='testpassword123')
        
        data = {
            'isi_komentar': 'anjing'
        }
        
        response = client.post(
            reverse('komentar:add_komentar', args=[setup_resep.id]),
            data=data,
            follow=True
        )
        
        assert response.status_code == 200
        assert not Komentar.objects.filter(
            user=setup_users['regular_user'],
            resep=setup_resep,
            isi_komentar__contains='anjing'
        ).exists()
        messages = list(response.context.get('messages', []))
        assert any('prohibited words' in str(message) for message in messages), "No error message about prohibited words"
    
    def test_add_komentar_admin_blocked(self, setup_users, setup_resep, client):
        """Test that admins cannot add comments"""
        client.login(username='adminuser', password='adminpassword123')
        
        data = {
            'isi_komentar': 'This is an admin comment'
        }
        
        response = client.post(
            reverse('komentar:add_komentar', args=[setup_resep.id]),
            data=data,
            follow=True
        )
        
        assert response.status_code == 200
        assert not Komentar.objects.filter(
            isi_komentar='This is an admin comment'
        ).exists()
        
        messages = list(response.context.get('messages', []))
        assert any('Admin accounts cannot add comments' in str(message) for message in messages)
    
    @patch('komentar.views.check_rate_limit')
    def test_add_komentar_rate_limit(self, mock_rate_limit, setup_users, setup_resep, client):
        mock_rate_limit.return_value = True 
        client.login(username='testuser', password='testpassword123')
        
        data = {
            'isi_komentar': 'This comment should be rate limited'
        }
        
        response = client.post(
            reverse('komentar:add_komentar', args=[setup_resep.id]),
            data=data,
            follow=True
        )
        
        assert response.status_code == 200
        assert not Komentar.objects.filter(
            isi_komentar='This comment should be rate limited'
        ).exists()

        messages = list(response.context.get('messages', []))
        assert any('melebihi batas komentar' in str(message) for message in messages)


class TestDeleteKomentar:   
    def test_delete_komentar_success(self, setup_users, setup_komentar, client):
        client.login(username='testuser', password='testpassword123')
        
        comment_id = setup_komentar.id
        response = client.post(
            reverse('komentar:delete_komentar', args=[comment_id]),
            follow=True
        )
        
        assert response.status_code == 200
        assert not Komentar.objects.filter(id=comment_id).exists()

        messages = list(response.context.get('messages', []))
        assert any('Komentar berhasil dihapus' in str(message) for message in messages)
    
    def test_delete_komentar_unauthorized(self, setup_users, setup_komentar, client):
        client.login(username='otheruser', password='testpassword123')
        
        comment_id = setup_komentar.id
        response = client.post(
            reverse('komentar:delete_komentar', args=[comment_id]),
            follow=True
        )
        
        assert response.status_code == 200
        assert Komentar.objects.filter(id=comment_id).exists()
    
        messages = list(response.context.get('messages', []))
        assert any('You can only delete your own comments' in str(message) for message in messages)
        
    def test_delete_komentar_admin_blocked(self, setup_users, setup_komentar, client):
        client.login(username='adminuser', password='adminpassword123')
        
        comment_id = setup_komentar.id
        response = client.post(
            reverse('komentar:delete_komentar', args=[comment_id]),
            follow=True
        )
        
        assert response.status_code == 200
        assert Komentar.objects.filter(id=comment_id).exists()
        
        messages = list(response.context.get('messages', []))
        assert any('Admin can only delete comments from the admin dashboard' in str(message) for message in messages)


class TestReportComment:    
    def test_report_comment_success(self, setup_users, setup_komentar, client):
        client.login(username='otheruser', password='testpassword123')
        
        data = {
            'reason': 'offensive'
        }
        
        response = client.post(
            reverse('komentar:report_comment', args=[setup_komentar.id]),
            data=data,
            follow=True
        )
        
        assert response.status_code == 200
        assert Report.objects.filter(
            reporter=setup_users['other_user'],
            comment=setup_komentar,
            reason='offensive'
        ).exists()
    
        messages = list(response.context.get('messages', []))
        assert any('Comment reported successfully' in str(message) for message in messages)
    
    def test_report_comment_invalid_reason(self, setup_users, setup_komentar, client):
        """Test reporting with invalid reason"""
        client.login(username='otheruser', password='testpassword123')
        
        data = {
            'reason': 'not_a_valid_reason'
        }
        
        response = client.post(
            reverse('komentar:report_comment', args=[setup_komentar.id]),
            data=data,
            follow=True
        )
        
        assert response.status_code == 200
        assert not Report.objects.filter(
            reporter=setup_users['other_user'],
            comment=setup_komentar
        ).exists()
        
        messages = list(response.context.get('messages', []))
        assert any('Invalid report reason' in str(message) for message in messages)
    
    def test_report_comment_already_reported(self, setup_users, setup_komentar, client):
        Report.objects.create(
            reporter=setup_users['other_user'],
            comment=setup_komentar,
            reason='offensive',
            status='pending'
        )
        
        client.login(username='otheruser', password='testpassword123')
        
        data = {
            'reason': 'spam' 
        }
        
        response = client.post(
            reverse('komentar:report_comment', args=[setup_komentar.id]),
            data=data,
            follow=True
        )
        
        assert response.status_code == 200
        assert Report.objects.filter(
            reporter=setup_users['other_user'],
            comment=setup_komentar
        ).count() == 1
        
        messages = list(response.context.get('messages', []))
        assert any('already reported' in str(message) for message in messages)
    
    def test_report_comment_admin_blocked(self, setup_users, setup_komentar, client):
        client.login(username='adminuser', password='adminpassword123')
        
        data = {
            'reason': 'offensive'
        }
        
        response = client.post(
            reverse('komentar:report_comment', args=[setup_komentar.id]),
            data=data,
            follow=True
        )
        
        assert response.status_code == 200
        assert not Report.objects.filter(
            reporter=setup_users['admin_user'],
            comment=setup_komentar
        ).exists()
        
        messages = list(response.context.get('messages', []))
        assert any('Admin accounts cannot report comments' in str(message) for message in messages)


class TestAdminModeration:
    
    def test_admin_moderate_delete_comment(self, setup_users, setup_komentar, client):
        """Test admin moderating and deleting a comment"""
        tastify_user, created = User.objects.get_or_create(
            username='Tastify',
            defaults={
                'is_active': False,
                'email': 'system@tastify.example.com'
            }
        )
        
        client.login(username='adminuser', password='adminpassword123')
        
        data = {
            'reason': 'offensive',
            'action': 'delete_comment'
        }
        
        response = client.post(
            reverse('komentar:admin_moderate_comment', args=[setup_komentar.id]),
            data=data,
            follow=True
        )
        
        assert response.status_code == 200
        assert not Komentar.objects.filter(id=setup_komentar.id).exists()
        assert Report.objects.filter(
            reason='offensive',
            status='deleted'
        ).exists()

        messages = list(response.context.get('messages', []))
        assert any('Comment has been deleted' in str(message) for message in messages)
    
    def test_admin_moderate_ban_user(self, setup_users, setup_komentar, client):
        tastify_user, created = User.objects.get_or_create(
            username='Tastify',
            defaults={
                'is_active': False,
                'email': 'system@tastify.example.com'
            }
        )
        
        another_comment = Komentar.objects.create(
            user=setup_users['regular_user'],
            resep=setup_komentar.resep,
            isi_komentar='Another test comment'
        )
        
        client.login(username='adminuser', password='adminpassword123')
        
        data = {
            'reason': 'harassment',
            'action': 'ban_user'
        }
        
        response = client.post(
            reverse('komentar:admin_moderate_comment', args=[setup_komentar.id]),
            data=data,
            follow=True
        )
        
        assert response.status_code == 200
        assert not Komentar.objects.filter(user=setup_users['regular_user']).exists()
        setup_users['regular_user'].refresh_from_db()
        assert not setup_users['regular_user'].is_active
        assert Report.objects.filter(
            status='banned',
            reason='harassment'
        ).exists()
    
        messages = list(response.context.get('messages', []))
        assert any('has been banned' in str(message) for message in messages)
    
    def test_non_admin_cannot_moderate(self, setup_users, setup_komentar, client):
        client.login(username='testuser', password='testpassword123')
        
        data = {
            'reason': 'offensive',
            'action': 'delete_comment'
        }
        
        response = client.post(
            reverse('komentar:admin_moderate_comment', args=[setup_komentar.id]),
            data=data,
            follow=True
        )
        
        assert response.status_code == 200
        assert Komentar.objects.filter(id=setup_komentar.id).exists()
        messages = list(response.context.get('messages', []))
        assert any('Only admin can use this feature' in str(message) for message in messages)


class TestUtilityFunctions:
    def test_check_rate_limit_first_request(self):
        cache.clear()
        
        result = check_rate_limit(999, 'test_action', 5, 3600)
        assert result is False 
    
    def test_check_rate_limit_exceeding(self):
        """Test exceeding rate limit"""
        cache.clear()
        
        user_id = 888
        action = 'test_action2'
        max_attempts = 3
        period = 3600
        for _ in range(max_attempts):
            result = check_rate_limit(user_id, action, max_attempts, period)
            assert result is False
        result = check_rate_limit(user_id, action, max_attempts, period)
        assert result is True
    
    def test_contains_offensive_words_clean(self):
        text = "resepnya enak"
        has_offensive, word = contains_offensive_words(text)
        
        assert has_offensive is False
        assert word is None
    
    def test_contains_offensive_words_offensive(self):
        text = "anjing"
        has_offensive, word = contains_offensive_words(text)
        
        assert has_offensive is True
        assert word == 'anjing'
    
    def test_sanitize_html_allowed_tags(self):
        """Test HTML sanitization with allowed tags"""
        html = "<p>This is <b>bold</b> and <i>italic</i> text.</p>"
        sanitized = sanitize_html(html)
    
        assert "<p>" in sanitized
        assert "<b>" in sanitized
        assert "<i>" in sanitized
    
    def test_sanitize_html_disallowed_tags(self):
        """Test HTML sanitization with disallowed tags"""
        html = "<script>alert('XSS');</script><p>Normal text</p>"
        sanitized = sanitize_html(html)

        assert "<script>" not in sanitized
        assert "<p>" in sanitized

import pytest
from django.test import RequestFactory, Client
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.messages import get_messages
from django.utils import timezone
from django.urls import reverse
from django.db.models import Avg, Count
import random

from resep.models import Resep, Kategori, Bahan, CookingMethod
from rating.models import Rating
from authentication.models import AdminAccessLog, UserProfile
from komentar.models import Report, Komentar
from main.views import show_main, admin_dashboard, is_admin

# Fixtures for database setup
@pytest.fixture
def user_profiles():
    """Create regular users and user profiles for testing"""
    # regular users
    user1 = User.objects.create_user(username='testuser1', email='test1@example.com', password='12345')
    user2 = User.objects.create_user(username='testuser2', email='test2@example.com', password='12345')
    
    # user profiles for the users
    profile1 = UserProfile.objects.create(user=user1, bio='Test user 1')
    profile2 = UserProfile.objects.create(user=user2, bio='Test user 2')
    
    return [profile1, profile2]

@pytest.fixture
def admin_user():
    admin = User.objects.create_user(
        username='admin', 
        email='admin@example.com',
        password='adminpass',
        is_staff=True,
        is_superuser=True
    )
    
    admin_profile = UserProfile.objects.create(
        user=admin,
        bio='Admin user for testing'
    )
    
    return admin

@pytest.fixture
def recipes(user_profiles):
    kategori = Kategori.objects.create(nama="Dessert")
    metode_masak = CookingMethod.objects.create(nama="Baking")
    bahan_utama = Bahan.objects.create(nama="Flour")
    
    recipes = []
    for i in range(10):
        recipe = Resep.objects.create(
            judul=f"Test Recipe {i}",
            deskripsi=f"This is test recipe {i}",
            bahan=f"Ingredient {i}",
            langkah=f"Step {i}",
            alat=f"Tool {i}",
            kategori=kategori,
            metode_masak=metode_masak,
            bahan_utama=bahan_utama,
            url_foto=f'https://example.com/recipe{i}.jpg',
            durasi=30,
            porsi=4,
            user=user_profiles[0]
        )
        recipes.append(recipe)
    
    return recipes

@pytest.fixture
def ratings(recipes, user_profiles):
    """Create ratings for recipes"""
    ratings = []
    
    for i, recipe in enumerate(recipes[:5]):
        user_profile1, user_profile2 = user_profiles
        
        # User 1 rates
        rating1 = Rating.objects.create(
            user=user_profile1.user,
            resep=recipe,
            score=(i % 5) + 1  
        )
        
        # User 2 rates
        rating2 = Rating.objects.create(
            user=user_profile2.user,
            resep=recipe,
            score=((i + 2) % 5) + 1 
        )
        
        ratings.extend([rating1, rating2])
    
    return ratings

@pytest.fixture
def reported_comments(recipes, user_profiles):
    """Create comments and reports for testing"""
    user_profile1, user_profile2 = user_profiles
    comments = []
    reports = []
    
    for i, recipe in enumerate(recipes[:3]):
        comment = Komentar.objects.create(
            user=user_profile1.user,
            resep=recipe,
            isi_komentar=f"Test comment {i} for recipe {recipe.judul}",
            created_at=timezone.now()
        )
        comments.append(comment)
        
        if i % 2 == 0:  
            report = Report.objects.create(
                reporter=user_profile2.user,
                comment=comment,
                reason='offensive',  
                status='pending',  
                created_at=timezone.now()
            )
            report.save_comment_info()  
            reports.append(report)
    
    return reports

@pytest.mark.django_db
def test_show_main_anonymous_user(recipes, ratings):
    """Test the show_main view with an anonymous user"""
    client = Client()
    
    response = client.get('/')
    
    assert response.status_code == 200
    
    assert 'main.html' in [t.name for t in response.templates]
    
    assert 'user' in response.context
    assert 'latest_recipes' in response.context
    assert 'top_rated_recipes' in response.context
    assert 'random_recipes' in response.context
    
    assert len(response.context['latest_recipes']) <= 5
    
    if response.context['top_rated_recipes']:
        assert len(response.context['top_rated_recipes']) <= 5
        for recipe in response.context['top_rated_recipes']:
            assert hasattr(recipe, 'average_rating_rounded')
    
    assert len(response.context['random_recipes']) <= 5

@pytest.mark.django_db
def test_show_main_logged_in_user(recipes, ratings, user_profiles):
    user_profile = user_profiles[0]
    
    client = Client()
    client.force_login(user_profile.user)
    
    response = client.get('/')
    
    assert response.status_code == 200
    
    assert response.context['user'] == user_profile.user

@pytest.mark.django_db
def test_show_main_no_recipes():
    Resep.objects.all().delete()
    
    client = Client()
    
    response = client.get('/')
    
    assert response.status_code == 200
    
    assert len(response.context['latest_recipes']) == 0
    assert len(response.context['top_rated_recipes']) == 0
    assert len(response.context['random_recipes']) == 0

@pytest.mark.django_db
def test_admin_dashboard_as_admin(admin_user, user_profiles, reported_comments):
    client = Client()
    client.force_login(admin_user)
    
    response = client.get('/admin-dashboard/')
    
    assert response.status_code == 200
    
    assert 'user_profiles' in response.context
    assert 'reported_comments' in response.context
    
    assert len(response.context['user_profiles']) >= len(user_profiles)
    
    assert len(response.context['reported_comments']) == len(reported_comments)
    
    logs = AdminAccessLog.objects.filter(admin_user=admin_user, action="Viewed user profiles")
    assert logs.exists()

@pytest.mark.django_db
def test_admin_dashboard_as_regular_user(user_profiles):
    user_profile = user_profiles[0]
    
    client = Client()
    client.force_login(user_profile.user)
    
    response = client.get('/admin-dashboard/')
    
    assert response.status_code in [302, 403]

@pytest.mark.django_db
def test_admin_dashboard_unauthenticated():
    client = Client()
    
    response = client.get('/admin-dashboard/')
    
    assert response.status_code == 302

def test_is_admin_with_superuser():
    user = User(is_superuser=True, is_staff=False)
    assert is_admin(user) is True
    
def test_is_admin_with_staff():
    user = User(is_superuser=False, is_staff=True)
    assert is_admin(user) is True
    
def test_is_admin_with_regular_user():
    user = User(is_superuser=False, is_staff=False)
    assert is_admin(user) is False

@pytest.mark.django_db
def test_delete_comment(admin_user, reported_comments):
    """Test the delete_comment view"""
    assert len(reported_comments) > 0
    report = reported_comments[0]
    
    comment_id = report.comment.id
    
    client = Client()
    client.force_login(admin_user)
    
    response = client.post(reverse('main:delete_comment', args=[report.id]))
    
    assert response.status_code == 302
    assert response.url == reverse('main:admin_dashboard')
    
    report.refresh_from_db()
    assert report.status == 'deleted'
    
    assert report.comment_info is not None
    
    with pytest.raises(Komentar.DoesNotExist):
        deleted_comment = Komentar.objects.get(id=comment_id)

@pytest.mark.django_db
def test_ignore_report(admin_user, reported_comments):
    """Test the ignore_report view"""
    assert len(reported_comments) > 0
    report = reported_comments[0]
    
    client = Client()
    client.force_login(admin_user)
    
    comment_id = report.comment.id
    
    response = client.post(reverse('main:ignore_report', args=[report.id]))
    
    assert response.status_code == 302
    assert response.url == reverse('main:admin_dashboard')
    
    report.refresh_from_db()
    assert report.status == 'ignore'
    
    assert Komentar.objects.filter(id=comment_id).exists()

@pytest.mark.django_db
def test_ban_user(admin_user, user_profiles, reported_comments):
    """Test the ban_user view"""
    user_profile = user_profiles[0]
    user = user_profile.user
    
    assert user.is_active == True
    
    comment_count = Komentar.objects.filter(user=user).count()
    assert comment_count > 0
    
    client = Client()
    client.force_login(admin_user)
    
    response = client.post(reverse('main:ban_user', args=[user.id]))
    
    assert response.status_code == 302
    assert response.url == reverse('main:admin_dashboard')
    
    user.refresh_from_db()
    assert user.is_active == False
    
    assert Komentar.objects.filter(user=user).count() == 0
    
    for report in Report.objects.filter(comment__user=user):
        assert report.status == 'banned'

@pytest.mark.django_db
def test_clear_report_history(admin_user, reported_comments):
    """Test the clear_report_history view"""
    report = reported_comments[0]
    report.status = 'deleted'
    report.save()
    
    if len(reported_comments) > 1:
        report2 = reported_comments[1]
        report2.status = 'ignore'
        report2.save()
    
    non_pending_count = Report.objects.exclude(status='pending').count()
    assert non_pending_count > 0
    
    client = Client()
    client.force_login(admin_user)
    
    response = client.post(reverse('main:clear_report_history'))
    
    assert response.status_code == 302
    assert response.url == reverse('main:admin_dashboard')
    
    assert Report.objects.exclude(status='pending').count() == 0
    
    pending_count = Report.objects.filter(status='pending').count()
    assert pending_count >= 0 
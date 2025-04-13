import pytest
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache
from unittest.mock import patch, MagicMock

from authentication.models import UserProfile
from resep.models import Resep, Kategori, Bahan, CookingMethod
from bookmark.models import Bookmark
from bookmark.views import toggle_bookmark, bookmark_list, check_bookmark_status

@pytest.fixture
def setup_user():
    """Fixture to create a test user and userprofile."""
    user = User.objects.create_user(username='testuser', password='password123')
    user_profile = UserProfile.objects.create(user=user)
    return user, user_profile

@pytest.fixture
def setup_recipe_data():
    """Fixture to create test categories, ingredients, cooking methods."""
    kategori = Kategori.objects.create(nama='Test Category')
    bahan = Bahan.objects.create(nama='Test Ingredient')
    cooking_method = CookingMethod.objects.create(nama='Test Method')
    return kategori, bahan, cooking_method

@pytest.fixture
def setup_recipe(setup_user, setup_recipe_data):
    """Fixture to create a test recipe."""
    _, user_profile = setup_user
    kategori, bahan, cooking_method = setup_recipe_data
    
    recipe = Resep.objects.create(
        judul='Test Recipe',
        deskripsi='Test description',
        user=user_profile,
        alat='Test tools',
        bahan='Test ingredients',
        langkah='Test steps',
        kategori=kategori,
        metode_masak=cooking_method,
        bahan_utama=bahan,
        url_foto='http://example.com/photo.jpg',
        durasi=30,
        porsi=4,
        likes_count=0
    )
    return recipe

@pytest.fixture
def authenticated_client(setup_user):
    """Fixture for an authenticated client."""
    user, _ = setup_user
    client = Client()
    client.login(username='testuser', password='password123')
    return client

@pytest.fixture
def setup_bookmark(setup_user, setup_recipe):
    """Fixture to create a test bookmark."""
    _, user_profile = setup_user
    recipe = setup_recipe
    
    bookmark = Bookmark.objects.create(
        user=user_profile,
        resep=recipe,
        created_at=timezone.now()
    )
    return bookmark

@pytest.fixture
def clear_cache():
    """Fixture to clear cache before and after tests."""
    cache.clear()
    yield
    cache.clear()

class TestBookmarkModel:
    @pytest.mark.django_db
    def test_bookmark_creation(self, setup_bookmark):
        """Test bookmark model creation."""
        bookmark = setup_bookmark
        assert isinstance(bookmark, Bookmark)
        assert str(bookmark) == f"{bookmark.user.user.username} - {bookmark.resep.judul}"

    @pytest.mark.django_db
    def test_update_view_timestamp(self, setup_bookmark):
        """Test updating the last viewed timestamp."""
        bookmark = setup_bookmark
        assert bookmark.last_viewed_at is None
        
        bookmark.update_view_timestamp()
        assert bookmark.last_viewed_at is not None

    @pytest.mark.django_db
    def test_unique_together_constraint(self, setup_user, setup_recipe):
        """Test the unique together constraint for user and recipe."""
        _, user_profile = setup_user
        recipe = setup_recipe
        
        # Create first bookmark
        Bookmark.objects.create(user=user_profile, resep=recipe)
        
        # Attempt to create duplicate bookmark
        with pytest.raises(Exception):  # Should raise an integrity error
            Bookmark.objects.create(user=user_profile, resep=recipe)

class TestBookmarkViews:
    @pytest.mark.django_db
    def test_bookmark_list_view(self, authenticated_client, setup_bookmark):
        """Test the bookmark list view."""
        response = authenticated_client.get(reverse('bookmark:list_bookmark'))
        
        assert response.status_code == 200
        assert 'bookmark_items' in response.context
        assert len(response.context['bookmark_items']) == 1

    @pytest.mark.django_db
    def test_bookmark_list_pagination(self, authenticated_client, setup_user, setup_recipe):
        """Test pagination in bookmark list view."""
        _, user_profile = setup_user
        recipe = setup_recipe
        
        # Create 15 bookmarks
        for i in range(15):
            new_recipe = Resep.objects.create(
                judul=f'Test Recipe {i}',
                deskripsi='Test description',
                user=user_profile,
                alat='Test tools',
                bahan='Test ingredients',
                langkah='Test steps',
                kategori=recipe.kategori,
                metode_masak=recipe.metode_masak,
                bahan_utama=recipe.bahan_utama,
                url_foto='http://example.com/photo.jpg',
                durasi=30,
                porsi=4
            )
            Bookmark.objects.create(user=user_profile, resep=new_recipe)
        
        # Test first page with default 9 items
        response = authenticated_client.get(reverse('bookmark:list_bookmark'))
        assert response.status_code == 200
        assert len(response.context['bookmark_items']) == 9
        
        # Test second page
        response = authenticated_client.get(reverse('bookmark:list_bookmark') + '?page=2')
        assert response.status_code == 200
        assert len(response.context['bookmark_items']) == 6
        
        # Test with different items_per_page
        response = authenticated_client.get(reverse('bookmark:list_bookmark') + '?items_per_page=18')
        assert response.status_code == 200
        assert len(response.context['bookmark_items']) == 15  # All items fit on one page

    @pytest.mark.django_db
    def test_bookmark_list_sorting(self, authenticated_client, setup_user, setup_recipe):
        """Test sorting in bookmark list view."""
        _, user_profile = setup_user
        recipe = setup_recipe
        
        # Create bookmarks with different times
        for i in range(3):
            new_recipe = Resep.objects.create(
                judul=f'Test Recipe {i}',
                deskripsi='Test description',
                user=user_profile,
                alat='Test tools',
                bahan='Test ingredients',
                langkah='Test steps',
                kategori=recipe.kategori,
                metode_masak=recipe.metode_masak,
                bahan_utama=recipe.bahan_utama,
                url_foto='http://example.com/photo.jpg',
                durasi=30,
                porsi=4
            )
            bookmark = Bookmark.objects.create(user=user_profile, resep=new_recipe)
            # Adjust creation timestamp to ensure order
            bookmark.created_at = timezone.now() - timezone.timedelta(days=i)
            bookmark.save()
        
        # Test newest first (default)
        response = authenticated_client.get(reverse('bookmark:list_bookmark'))
        bookmarks = list(response.context['bookmark_items'])
        assert bookmarks[0].created_at > bookmarks[-1].created_at
        
        # Test oldest first
        response = authenticated_client.get(reverse('bookmark:list_bookmark') + '?sort=oldest')
        bookmarks = list(response.context['bookmark_items'])
        assert bookmarks[0].created_at < bookmarks[-1].created_at

    @pytest.mark.django_db
    def test_toggle_bookmark_create(self, authenticated_client, setup_recipe, clear_cache):
        """Test creating a bookmark via toggle_bookmark view."""
        recipe = setup_recipe
        
        response = authenticated_client.post(
            reverse('bookmark:toggle_bookmark', kwargs={'resep_id': recipe.id}),
            {},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['is_bookmarked'] is True
        assert data['bookmarks_count'] == 1
        assert Bookmark.objects.count() == 1

    @pytest.mark.django_db
    def test_toggle_bookmark_delete(self, authenticated_client, setup_bookmark, clear_cache):
        """Test deleting a bookmark via toggle_bookmark view."""
        bookmark = setup_bookmark
        
        response = authenticated_client.post(
            reverse('bookmark:toggle_bookmark', kwargs={'resep_id': bookmark.resep.id}),
            {},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['is_bookmarked'] is False
        assert data['bookmarks_count'] == 0
        assert Bookmark.objects.count() == 0
    
    @pytest.mark.django_db
    def test_toggle_bookmark_error_handling(self, authenticated_client, setup_recipe, clear_cache):
        """Test error handling in toggle_bookmark view."""
        recipe = setup_recipe
        
        with patch('bookmark.views.Bookmark.objects.filter', side_effect=Exception('Test error')):
            response = authenticated_client.post(
                reverse('bookmark:toggle_bookmark', kwargs={'resep_id': recipe.id}),
                {},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            
            assert response.status_code == 500
            data = response.json()
            assert 'error' in data

    @pytest.mark.django_db
    def test_check_bookmark_status(self, authenticated_client, setup_bookmark):
        """Test checking bookmark status."""
        bookmark = setup_bookmark
        
        response = authenticated_client.get(
            reverse('bookmark:check_bookmark_status', kwargs={'resep_id': bookmark.resep.id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['is_bookmarked'] is True
        assert data['bookmark_count'] == 1

    @pytest.mark.django_db
    def test_bookmark_rate_limiting(self, authenticated_client, setup_recipe, clear_cache):
        """Test rate limiting for bookmark toggle."""
        recipe = setup_recipe
    
        with patch('bookmark.views.rate_limit_bookmark', return_value=lambda func: lambda *args, **kwargs: func(*args, **kwargs)):
            with patch('django.core.cache.cache.get', return_value={'count': 11, 'window_start': timezone.now().timestamp() - 30}):
                with patch('django.core.cache.cache.set'):
                    response = authenticated_client.post(
                        reverse('bookmark:toggle_bookmark', kwargs={'resep_id': recipe.id}),
                        {},
                        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
                    )
                    assert response.status_code == 429

    @pytest.mark.django_db
    def test_unauthorized_access(self, setup_recipe):
        """Test unauthorized access to bookmark endpoints."""
        client = Client()  # Unauthenticated client
        recipe = setup_recipe
        
        # Try to access bookmark list
        response = client.get(reverse('bookmark:list_bookmark'))
        assert response.status_code == 302  # Redirect to login
        
        # Try to toggle bookmark
        response = client.post(
            reverse('bookmark:toggle_bookmark', kwargs={'resep_id': recipe.id}),
            {},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        assert response.status_code == 302  

    @pytest.mark.django_db
    def test_resep_update_likes_count(self, setup_recipe, setup_user):
        """Test that recipe likes_count is updated when bookmarks change."""
        recipe = setup_recipe
        _, user_profile = setup_user
        
        # default
        assert recipe.likes_count == 0
        
        # Create bookmark
        bookmark = Bookmark.objects.create(user=user_profile, resep=recipe)
        recipe.update_likes_count()
        recipe.refresh_from_db()
        assert recipe.likes_count == 1
        
        # Delete bookmark
        bookmark.delete()
        recipe.update_likes_count()
        recipe.refresh_from_db()
        assert recipe.likes_count == 0

    @pytest.mark.django_db
    def test_bookmark_recipe_detail(self, authenticated_client, setup_bookmark):
        """Test bookmark status is correctly retrieved in recipe detail view."""
        bookmark = setup_bookmark
        recipe = bookmark.resep
        
        # Access the recipe detail page
        response = authenticated_client.get(
            reverse('resep:detail_resep', kwargs={'id': recipe.id})
        )
        
        # Verify the response and bookmark status
        assert response.status_code == 200
        assert response.context['is_bookmarked'] is True
        
        # Delete the bookmark
        bookmark.delete()
        
        # Access the recipe detail page again
        response = authenticated_client.get(
            reverse('resep:detail_resep', kwargs={'id': recipe.id})
        )
        
        # Verify bookmark status is now False
        assert response.status_code == 200
        assert response.context['is_bookmarked'] is False
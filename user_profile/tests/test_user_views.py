import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from authentication.models import UserProfile
from resep.models import Resep

User = get_user_model()

@pytest.mark.django_db
class TestProfileViews:

    def setup_method(self):
        self.regular_user = User.objects.create_user(username="testuser", password="testpass")
        self.staff_user = User.objects.create_user(username="staffuser", password="testpass", is_staff=True)
        UserProfile.objects.create(user=self.regular_user)
        UserProfile.objects.create(user=self.staff_user)

    def test_redirect_if_not_logged_in(self, client):
        url = reverse('user_profile:profile')
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url

    def test_regular_user_can_access_profile(self, client):
        client.login(username="testuser", password="testpass")
        url = reverse('user_profile:profile')
        response = client.get(url)
        assert response.status_code == 200
        assert "profile.html" in [t.name for t in response.templates]

    def test_ajax_post_profile_update_success_or_fail(self, client):
        client.login(username="testuser", password="testpass")
        url = reverse('user_profile:profile')
        headers = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        data = {
            "username": "newusername",
            "bio": "new bio"  # sesuaikan dengan field ProfileUpdateForm
        }
        response = client.post(url, data, **headers)
        assert response.status_code == 200
        assert "success" in response.json()

    def test_profile_detail_view(self, client):
        client.login(username="testuser", password="testpass")
        url = reverse('user_profile:profile_detail')
        response = client.get(url)
        assert response.status_code == 200
        assert "profile_detail.html" in [t.name for t in response.templates]

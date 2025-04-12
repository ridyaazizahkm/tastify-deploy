#baru nyoba
import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from authentication.models import UserProfile
from resep.models import Resep

@pytest.mark.django_db
def create_user_with_profile():
    user = User.objects.create_user(username='testuser', password='testpass')
    profile = UserProfile.objects.create(user=user)
    return user, profile

@pytest.mark.django_db
def test_profile_get_authenticated(client):
    user, profile = create_user_with_profile()
    client.login(username='testuser', password='testpass')

    url = reverse('user_profile:profile')  # Pastikan ini sesuai nama url di urls.py
    response = client.get(url)

    assert response.status_code == 200
    assert b'user_form' in response.content  # Bisa diubah jika render-nya beda

@pytest.mark.django_db
def test_profile_post_ajax_success(client):
    user, profile = create_user_with_profile()
    client.login(username='testuser', password='testpass')

    url = reverse('user_profile:profile')
    headers = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
    data = {
        'username': 'updateduser',
        'first_name': 'Updated',
        'last_name': 'User'
    }

    response = client.post(url, data=data, **headers)
    assert response.status_code == 200
    json_data = response.json()
    assert 'success' in json_data

@pytest.mark.django_db
def test_profile_staff_redirect(client):
    staff_user = User.objects.create_user(username='staff', password='testpass', is_staff=True)
    UserProfile.objects.create(user=staff_user)
    client.login(username='staff', password='testpass')

    url = reverse('user_profile:profile')
    response = client.get(url)

    # Should redirect away
    assert response.status_code == 302
    assert response.url == reverse('cards_makanan:restaurant_list')

@pytest.mark.django_db
def test_resep_detail_view(client):
    user, profile = create_user_with_profile()
    resep = Resep.objects.create(user=profile, title="Test Resep", deskripsi="Deskripsi")

    url = reverse('user_profile:resep_detail', args=[resep.pk])
    response = client.get(url)

    assert response.status_code == 200
    assert b"Test Resep" in response.content

@pytest.mark.django_db
def test_profile_detail_get(client):
    user, profile = create_user_with_profile()
    client.login(username='testuser', password='testpass')

    url = reverse('user_profile:profile_detail')
    response = client.get(url)

    assert response.status_code == 200

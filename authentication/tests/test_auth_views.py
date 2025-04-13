import datetime
import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.cache import cache

@pytest.mark.django_db
class TestAuthViews:

    def test_register_get(self, client):
        response = client.get(reverse('authentication:register'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_register_post_valid(self, client):
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
        }
        response = client.post(reverse('authentication:register'), data)
        assert response.status_code == 302
        assert response.url == reverse('authentication:login')
        assert User.objects.filter(username='newuser').exists()


    def test_register_post_invalid(self, client):
        data = {
            'username': 'user',
            'password1': '123',
            'password2': '456',
        }
        response = client.post(reverse('authentication:register'), data)
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors

    def test_login_get(self, client):
        response = client.get(reverse('authentication:login'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_login_post_valid(self, client, django_user_model):
        user = django_user_model.objects.create_user(username='testuser', password='strongpassword')
        data = {'username': 'testuser', 'password': 'strongpassword'}
        response = client.post(reverse('authentication:login'), data)
        assert response.status_code == 302
        assert response.url == reverse('main:show_main')

    def test_login_post_invalid(self, client):
        data = {'username': 'wronguser', 'password': 'wrongpass'}
        response = client.post(reverse('authentication:login'), data)
        assert response.status_code == 200
        assert 'Invalid username or password.' in response.content.decode()

    def test_login_rate_limit(self, client, settings):
        settings.CACHES['default'] = {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}
        ip_key = 'login_attempts_127.0.0.1'
        time_key = 'last_login_attempt_127.0.0.1'

        cache.set(ip_key, 3)
        cache.set(time_key, datetime.datetime.now())

        data = {'username': 'anyuser', 'password': 'any'}
        response = client.post(reverse('authentication:login'), data)
        assert response.status_code == 200
        assert 'Too many failed login attempts' in response.content.decode()

        cache.delete(ip_key)
        cache.delete(time_key)

    def test_logout(self, client, django_user_model):
        user = django_user_model.objects.create_user(username='testuser', password='testpass')
        client.login(username='testuser', password='testpass')
        response = client.get(reverse('authentication:logout'))
        assert response.status_code == 302
        assert response.url == reverse('main:show_main')

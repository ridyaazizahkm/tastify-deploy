import pytest
from django.contrib.auth.models import User
from authentication.models import UserProfile, Encryption, AdminAccessLog
from django.conf import settings
from cryptography.fernet import Fernet

@pytest.mark.django_db
class TestUserProfileModel:

    def test_user_profile_creation_and_encryption(self):
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        profile = UserProfile.objects.create(user=user)

        assert profile.encrypted_email is not None
        assert profile.encrypted_email != user.email

        decrypted_email = profile.get_email()
        assert decrypted_email == 'test@example.com'

    def test_profile_str_method(self):
        user = User.objects.create_user(username='myuser', email='user@example.com')
        profile = UserProfile.objects.create(user=user)
        assert str(profile) == 'myuser Profile'


@pytest.mark.django_db
class TestAdminAccessLogModel:

    def test_admin_access_log_creation(self):
        user = User.objects.create_superuser(username='admin', email='admin@example.com', password='adminpass')
        log = AdminAccessLog.objects.create(admin_user=user, action='Logged in', ip_address='127.0.0.1')

        assert log.action == 'Logged in'
        assert log.ip_address == '127.0.0.1'
        assert str(log).startswith('admin - Logged in')

def test_encryption_class():
    key = settings.ENCRYPTION_KEY
    enc = Encryption()
    assert enc.key == key

    original_text = "hello@example.com"
    encrypted = enc.encrypt(original_text)
    decrypted = enc.decrypt(encrypted)

    assert encrypted != original_text
    assert decrypted == original_text

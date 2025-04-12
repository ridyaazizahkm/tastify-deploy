import pytest
from django.contrib.auth.models import User
from authentication.forms import UserRegistrationForm, UserUpdateForm, ProfileUpdateForm
from authentication.models import UserProfile

@pytest.mark.django_db
class TestUserRegistrationForm:

    def test_valid_registration_form(self):
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'securepassword123',
            'password2': 'securepassword123'
        }
        form = UserRegistrationForm(data=form_data)
        assert form.is_valid()

    def test_invalid_email_format(self):
        form_data = {
            'username': 'testuser',
            'email': 'invalid<>email.com',
            'password1': 'securepassword123',
            'password2': 'securepassword123'
        }
        form = UserRegistrationForm(data=form_data)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_password_mismatch(self):
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'password123',
            'password2': 'differentpassword'
        }
        form = UserRegistrationForm(data=form_data)
        assert not form.is_valid()
        assert 'password2' in form.errors

    def test_sanitized_username(self):
        form_data = {
            'username': '<script>',
            'email': 'test@example.com',
            'password1': 'securepassword123',
            'password2': 'securepassword123'
        }
        form = UserRegistrationForm(data=form_data)
        assert not form.is_valid()
        assert 'username' in form.errors


@pytest.mark.django_db
class TestUserUpdateForm:

    def test_update_user_form(self):
        user = User.objects.create_user(username='olduser', email='old@example.com', password='pass123')
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        form = UserUpdateForm(data=form_data, instance=user)
        assert form.is_valid()
        updated_user = form.save()
        assert updated_user.username == 'newuser'
        assert updated_user.email == 'new@example.com'


@pytest.mark.django_db
class TestProfileUpdateForm:

    def test_update_profile_bio(self):
        user = User.objects.create_user(username='testuser', password='pass123')
        profile = UserProfile.objects.create(user=user)
        form_data = {
            'bio': 'This is a test bio.'
        }
        form = ProfileUpdateForm(data=form_data, instance=profile)
        assert form.is_valid()
        updated_profile = form.save()
        assert updated_profile.bio == 'This is a test bio.'

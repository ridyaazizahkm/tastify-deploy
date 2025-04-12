import pytest
from authentication.forms import ProfileUpdateForm
from authentication.models import UserProfile
from django.contrib.auth.models import User

@pytest.mark.django_db
class TestProfileUpdateForm:

    def test_form_valid_data(self):
        user = User.objects.create_user(username='testuser', password='testpass')
        profile = UserProfile.objects.create(user=user)

        form_data = {'bio': 'This is a test bio.'}
        form = ProfileUpdateForm(data=form_data, instance=profile)

        assert form.is_valid()
        updated_profile = form.save()
        assert updated_profile.bio == 'This is a test bio.'

    def test_form_empty_bio(self):
        user = User.objects.create_user(username='testuser2', password='testpass')
        profile = UserProfile.objects.create(user=user)

        form_data = {'bio': ''}
        form = ProfileUpdateForm(data=form_data, instance=profile)

        assert form.is_valid()

    def test_form_missing_data(self):
        user = User.objects.create_user(username='testuser3', password='testpass')
        profile = UserProfile.objects.create(user=user)

        form = ProfileUpdateForm(data={}, instance=profile)
        # Karena bio optional, ini juga harus valid
        assert form.is_valid()

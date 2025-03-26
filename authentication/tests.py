from django.test import TestCase
from django.contrib.auth.models import User
from .forms import UserRegistrationForm

class XSSProtectionTest(TestCase):
    def test_xss_username_input(self):
        # Mencoba input script berbahaya
        form_data = {
            'username': '<script>alert("XSS")</script>',
            'email': 'test@example.com',
            'password1': 'SecurePassword123!',
            'password2': 'SecurePassword123!'
        }
        
        form = UserRegistrationForm(data=form_data)
        
        # Pastikan form tidak valid
        self.assertFalse(form.is_valid())
    
    def test_html_injection_prevention(self):
        form_data = {
            'username': '<img src=x onerror=alert("Hacked")>',
            'email': 'test@example.com',
            'password1': 'SecurePassword123!',
            'password2': 'SecurePassword123!'
        }
        
        form = UserRegistrationForm(data=form_data)
        
        # Pastikan form tidak valid
        self.assertFalse(form.is_valid())
    
    def test_safe_input_handling(self):
        form_data = {
            'username': 'validuser123',
            'email': 'safe@example.com',
            'password1': 'SecurePassword123!',
            'password2': 'SecurePassword123!'
        }
        
        form = UserRegistrationForm(data=form_data)
        
        # Pastikan form valid untuk input yang aman
        self.assertTrue(form.is_valid())
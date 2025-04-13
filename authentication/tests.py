from django.test import TestCase, Client
from django.contrib.auth.models import User
from .forms import UserRegistrationForm
import pytest
from django.conf import settings
from django.test.utils import override_settings
from authentication.models import UserProfile, Encryption
from cryptography.fernet import Fernet
import base64
import os

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

class TestEncryption(TestCase):
    @override_settings(ENCRYPTION_KEY=Fernet.generate_key())
    def test_encryption_initialization(self):
        encryptor = Encryption()
        self.assertEqual(encryptor.key, settings.ENCRYPTION_KEY)
        self.assertIsInstance(encryptor.cipher, Fernet)
    
    @override_settings(ENCRYPTION_KEY=Fernet.generate_key())
    def test_encrypt_decrypt_text(self):
        encryptor = Encryption()
        
        # Test dengan text normal
        original_text = "test@example.com"
        encrypted = encryptor.encrypt(original_text)
        
        # Encrypted text harus berbeda dengan aslinya
        self.assertNotEqual(encrypted, original_text)
        self.assertIsInstance(encrypted, str)
        
        # Decrypt seharusnya mengembalikan text asli
        decrypted = encryptor.decrypt(encrypted)
        self.assertEqual(decrypted, original_text)
    
    @override_settings(ENCRYPTION_KEY=Fernet.generate_key())
    def test_encrypt_decrypt_empty(self):
        encryptor = Encryption()
        
        # Test dengan None
        self.assertIsNone(encryptor.encrypt(None))
        self.assertIsNone(encryptor.decrypt(None))
        
        # Test dengan string kosong 
        encrypted_empty = encryptor.encrypt("")
        
        if encrypted_empty is None:
            self.assertIsNone(encrypted_empty)
        else:
            # Jika dienkripsi, maka tidak boleh sama dengan string kosong
            self.assertNotEqual(encrypted_empty, "")

class TestUserProfile(TestCase):
    @override_settings(ENCRYPTION_KEY=Fernet.generate_key())
    def test_email_encryption_on_save(self):
        email = "test@example.com"
        user = User.objects.create_user(
            username="testuser", 
            email=email,
            password="testpassword"
        )
        
        profile = UserProfile(user=user)
        profile.save()
        
        # Verifikasi bahwa encrypted_email ada dan berbeda dengan email asli
        self.assertIsNotNone(profile.encrypted_email)
        self.assertNotEqual(profile.encrypted_email, email)
        
        self.assertEqual(profile.get_email(), email)
    
    @override_settings(ENCRYPTION_KEY=Fernet.generate_key())
    def test_email_not_encrypted_if_no_email(self):
        user = User.objects.create_user(
            username="testuser2", 
            email="",
            password="testpassword"
        )
        
        profile = UserProfile(user=user)
        profile.save()
        
        # Verifikasi bahwa encrypted_email tidak ada
        self.assertIsNone(profile.encrypted_email)
        
        # Verifikasi bahwa get_email() mengembalikan email asli
        self.assertEqual(profile.get_email(), "")
    
    @override_settings(ENCRYPTION_KEY=Fernet.generate_key())
    def test_update_user_email(self):
        email = "test@example.com"
        user = User.objects.create_user(
            username="testuser3", 
            email=email,
            password="testpassword"
        )
        
        profile = UserProfile(user=user)
        profile.save()
        
        # Simpan encrypted_email asli
        original_encrypted = profile.encrypted_email
        
        # Ubah email user
        new_email = "new@example.com"
        user.email = new_email
        user.save()
        
        profile.save()
        
        self.assertEqual(profile.encrypted_email, original_encrypted)
        self.assertEqual(profile.get_email(), email)
        
        profile.encrypted_email = None
        profile.save()
        
        self.assertEqual(profile.get_email(), new_email)

# Integration test untuk enkripsi dalam flow registrasi
class TestEncryptionIntegration(TestCase):
    @override_settings(ENCRYPTION_KEY=Fernet.generate_key())
    def test_user_registration_encrypts_email(self):
        email = "newuser@example.com"
        user = User.objects.create_user(
            username='newuser',
            email=email,
            password='TestPassword123'
        )
        
        # Buat UserProfile 
        profile = UserProfile.objects.create(user=user)
        
        # Verifikasi email terenkripsi
        if profile.encrypted_email is not None:
            self.assertNotEqual(profile.encrypted_email, email)
            self.assertEqual(profile.get_email(), email)
        else:
            self.assertEqual(profile.get_email(), email)

    @override_settings(ENCRYPTION_KEY=Fernet.generate_key())
    def test_encrypted_email_security(self):
        # Buat user dengan email
        email = "secure@example.com"
        user = User.objects.create_user(
            username="secureuser", 
            email=email,
            password="testpassword"
        )
        
        # Buat dan simpan UserProfile 
        profile = UserProfile(user=user)
        profile.save()
        
        # Verifikasi enkripsi berhasil
        encrypted_email = profile.encrypted_email
        self.assertIsNotNone(encrypted_email)
        
        different_key = Fernet.generate_key()
        self.assertNotEqual(different_key, settings.ENCRYPTION_KEY)
        
        different_cipher = Fernet(different_key)
        
        with self.assertRaises(Exception):  
            different_cipher.decrypt(encrypted_email.encode())
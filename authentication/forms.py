from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from django.core.validators import RegexValidator

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-[#927155] focus:border-[#927155] block w-full p-2.5',
            'placeholder': 'john.doe@example.com',
        }),
        help_text="Enter a valid email address.",
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-[#927155] focus:border-[#927155] block w-full p-2.5',
            'placeholder': 'Your username',
        }),
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-[#927155] focus:border-[#927155] block w-full p-2.5',
            'placeholder': '•••••••••',
        }),
        help_text="Your password must contain at least 8 characters.",
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-[#927155] focus:border-[#927155] block w-full p-2.5',
            'placeholder': '•••••••••',
        }),
        help_text="Enter the same password as before, for verification.",
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-[#927155] focus:border-[#927155] block w-full p-2.5',
                'placeholder': 'Your username',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-[#927155] focus:border-[#927155] block w-full p-2.5',
                'placeholder': 'john.doe@example.com',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-[#927155] focus:border-[#927155] block w-full p-2.5',
                'placeholder': 'First name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-[#927155] focus:border-[#927155] block w-full p-2.5',
                'placeholder': 'Last name',
            }),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-[#927155] focus:border-[#927155] block w-full p-2.5',
                'placeholder': 'Write your thoughts here...',
                'rows': 4,
            }),
        }

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    username = forms.CharField(
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',  # Kombinasi validasi existing dan baru
                message='Username hanya boleh berisi huruf, angka, dan @/./+/-/_'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 sm:px-4 sm:py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#62191c] transition duration-300',
            'placeholder': 'Enter your username'
        })
    )
    
    email = forms.EmailField(
        validators=[
            RegexValidator(
                regex=r'^[^<>&\'"]+@[^<>&\'"]+\.[^<>&\'"]+$',
                message='Email mengandung karakter tidak valid'
            )
        ],
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 sm:px-4 sm:py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#62191c] transition duration-300',
            'placeholder': 'Enter your email'
        })
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 sm:px-4 sm:py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#62191c] transition duration-300',
            'placeholder': 'Enter your password'
        })
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 sm:px-4 sm:py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#62191c] transition duration-300',
            'placeholder': 'Confirm your password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def clean_username(self):
        username = self.cleaned_data['username']
        # Tambahan pembersihan dan validasi
        if any(char in username for char in '<>&\'"'):
            raise forms.ValidationError('Username mengandung karakter berbahaya')
        return username.strip()
    
    def clean_email(self):
        email = self.cleaned_data['email']
        # Tambahan pembersihan dan validasi
        if any(char in email for char in '<>&\'"'):
            raise forms.ValidationError('Email mengandung karakter berbahaya')
        return email.strip()
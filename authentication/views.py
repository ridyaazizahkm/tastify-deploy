import datetime
import re
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from .forms import UserRegistrationForm
from .models import UserProfile
from django.contrib.auth import authenticate, login as auth_login
from django.http import HttpResponse
from django.core import serializers
from django.core.cache import cache
from django.core.exceptions import ValidationError

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            messages.success(request, 'Account created successfully')
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
            if user is not None:
                login(request, user)
            return redirect('authentication:login')
        else:
            messages.error(request, 'Form is invalid')
            context = {'form': form}
            return render(request, 'register.html', context)

    else:
        form = UserRegistrationForm()
    context = {'form': form}
    return render(request, 'register.html', context)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class CustomAuthenticationForm(AuthenticationForm):
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Sanitize username to prevent SQL injection
        if username:
            username = re.sub(r'[<>&\'"()]', '', username)
            if not username:
                raise ValidationError('Invalid username')
        return username

def login_user(request):
    # Jika request menggunakan metode POST
    if request.method == 'POST':
        # Use the custom form with additional sanitization
        form = CustomAuthenticationForm(request, data=request.POST)

        # Additional server-side validation
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        
        # Remove potentially dangerous characters
        username = re.sub(r'[<>&\'"()]', '', username)
        password = re.sub(r'[<>&\'"()]', '', password)
        
        # Get client IP
        client_ip = get_client_ip(request)
        
        # Check login attempts cache
        login_attempts_key = f'login_attempts_{client_ip}'
        last_attempt_time_key = f'last_login_attempt_{client_ip}'
        
        # Retrieve login attempts and last attempt time
        login_attempts = cache.get(login_attempts_key, 0)
        last_attempt_time = cache.get(last_attempt_time_key)
        
        # If more than 3 failed attempts, check cooling down period
        if login_attempts >= 3:
            if last_attempt_time:
                # Check if 15 minutes have passed since last attempt
                time_since_last_attempt = datetime.datetime.now() - last_attempt_time
                if time_since_last_attempt.total_seconds() < 900:  # 15 minutes
                    messages.error(request, 'Too many failed login attempts. Please try again after 15 minutes.')
                    return render(request, 'login.html', {'form': AuthenticationForm(request)})
            
            # Reset attempts if cooling down period has passed
            cache.delete(login_attempts_key)
            cache.delete(last_attempt_time_key)
        
        # Jika request berasal dari web (form login)
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            
            # Clear any previous login attempt tracking for this IP
            cache.delete(login_attempts_key)
            cache.delete(last_attempt_time_key)
            
            response = HttpResponseRedirect(reverse("main:show_main"))
            response.set_cookie('last_login', str(datetime.datetime.now()))
            return response
        else:
            # Increment login attempts
            login_attempts += 1
            cache.set(login_attempts_key, login_attempts, 900)  # Store for 15 minutes
            cache.set(last_attempt_time_key, datetime.datetime.now(), 900)
            
            messages.error(request, 'Invalid username or password.')
            context = {'form': form}
            return render(request, 'login.html', context)

    else:
        form = AuthenticationForm(request)
        context = {'form': form}
        return render(request, 'login.html', context)

def logout_user(request):
    logout(request)
    response = HttpResponseRedirect(reverse('main:show_main'))
    response.delete_cookie('last_login')
    return response


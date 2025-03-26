import datetime
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

@csrf_exempt
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

@csrf_exempt
def login_user(request):
    # Jika request menggunakan metode POST
    if request.method == 'POST':
        # Jika request berasal dari web (form login)
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            response = HttpResponseRedirect(reverse("main:show_main"))
            response.set_cookie('last_login', str(datetime.datetime.now()))
            return response
        else:
            messages.error(request, 'Invalid username or password.')
            context = {'form': form}
            return render(request, 'login.html', context)

    else:
        form = AuthenticationForm(request)
        context = {'form': form}
        return render(request, 'login.html', context)

@csrf_exempt
def logout_user(request):
    logout(request)
    response = HttpResponseRedirect(reverse('main:show_main'))
    response.delete_cookie('last_login')
    return response


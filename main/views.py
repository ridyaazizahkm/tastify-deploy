from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required(login_url='authentication:login')
def show_main(request):
    context = {
        'npm' : '2306123456',
        'name': 'tastify',
        'class': 'PKPL'
    }

    return render(request, 'main.html', context)
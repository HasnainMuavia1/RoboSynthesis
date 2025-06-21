from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import login, authenticate

def home(request):
    """View function for the home page of the site."""
    return render(request, 'personalassistant/index.html')

def signup(request):
    """View function for user registration."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('personalassistant:home')
    else:
        form = UserCreationForm()
    return render(request, 'personalassistant/signup.html', {'form': form})

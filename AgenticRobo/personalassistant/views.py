from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required

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


def login_view(request):
    """View function for user login."""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('personalassistant:home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'personalassistant/login.html', {'form': form})


def logout_view(request):
    """View function for user logout."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('personalassistant:home')


@login_required
def profile(request):
    """View function for user profile."""
    return render(request, 'personalassistant/profile.html')

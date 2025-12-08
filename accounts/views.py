from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile, Achievement
from .decorators import admin_required

# Create your views here.

def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'accounts/login.html')

@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('login')

@login_required
def profile_view(request):
    """View user profile with achievements and stats"""
    profile = request.user.profile
    achievements = profile.achievements.all()
    
    context = {
        'profile': profile,
        'achievements': achievements,
    }
    return render(request, 'accounts/profile.html', context)

@admin_required
def user_management_view(request):
    """Admin view for managing users"""
    users = User.objects.select_related('profile').all()
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        
        if action == 'change_role':
            user = get_object_or_404(User, id=user_id)
            new_role = request.POST.get('role')
            user.profile.role = new_role
            user.profile.save()
            messages.success(request, f'Role updated for {user.username}')
        
        elif action == 'delete':
            user = get_object_or_404(User, id=user_id)
            if user != request.user:
                user.delete()
                messages.success(request, f'User {user.username} deleted')
            else:
                messages.error(request, 'Cannot delete your own account')
        
        return redirect('user_management')
    
    context = {
        'users': users,
    }
    return render(request, 'accounts/user_management.html', context)

@admin_required
def create_user_view(request):
    """Create new user"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        role = request.POST.get('role', 'SCOUTER')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        else:
            user = User.objects.create_user(username=username, password=password, email=email)
            user.profile.role = role
            user.profile.save()
            messages.success(request, f'User {username} created successfully')
            return redirect('user_management')
    
    return render(request, 'accounts/create_user.html')

from django.contrib import admin
from .models import UserProfile, Achievement

# Register your models here.

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'level', 'experience_points', 'prediction_points']
    list_filter = ['role', 'level']
    search_fields = ['user__username', 'user__email']

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'badge_type', 'description', 'earned_at']
    list_filter = ['badge_type', 'earned_at']
    search_fields = ['user_profile__user__username', 'description']

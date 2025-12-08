from django.contrib import admin
from .models import Event, Team, Match

# Register your models here.

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'event_code', 'start_date', 'end_date', 'api_source']
    list_filter = ['start_date', 'api_source']
    search_fields = ['name', 'event_code', 'location']

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['team_number', 'team_name', 'event', 'epa', 'win_rate']
    list_filter = ['event']
    search_fields = ['team_number', 'team_name']

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['event', 'match_number', 'match_type', 'scheduled_time', 'status', 'winner']
    list_filter = ['event', 'match_type', 'status']
    search_fields = ['match_number']

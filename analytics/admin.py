from django.contrib import admin
from .models import TeamAggregateStats, MatchAggregateStats

# Register your models here.

@admin.register(TeamAggregateStats)
class TeamAggregateStatsAdmin(admin.ModelAdmin):
    list_display = ['team', 'avg_overall_rating', 'matches_scouted', 'reliability_score', 'last_updated']
    list_filter = ['team__event']
    search_fields = ['team__team_number']

@admin.register(MatchAggregateStats)
class MatchAggregateStatsAdmin(admin.ModelAdmin):
    list_display = ['match', 'red_predicted_score', 'blue_predicted_score', 'calculated_at']
    list_filter = ['match__event']
    search_fields = ['match__match_number']

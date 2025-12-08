from django.contrib import admin
from .models import ScouterAssignment, MatchPrediction, ScoutingReport, QRCodeSubmission

# Register your models here.

@admin.register(ScouterAssignment)
class ScouterAssignmentAdmin(admin.ModelAdmin):
    list_display = ['match', 'scouter', 'position', 'team', 'assigned_at']
    list_filter = ['match__event', 'position']
    search_fields = ['scouter__username', 'team__team_number']

@admin.register(MatchPrediction)
class MatchPredictionAdmin(admin.ModelAdmin):
    list_display = ['scouter', 'match', 'predicted_winner', 'is_correct', 'points_awarded']
    list_filter = ['predicted_winner', 'is_correct']
    search_fields = ['scouter__username']

@admin.register(ScoutingReport)
class ScoutingReportAdmin(admin.ModelAdmin):
    list_display = ['match', 'scouter', 'team', 'overall_rating', 'confirmed', 'submitted_at']
    list_filter = ['confirmed', 'submitted_offline', 'match__event']
    search_fields = ['scouter__username', 'team__team_number']

@admin.register(QRCodeSubmission)
class QRCodeSubmissionAdmin(admin.ModelAdmin):
    list_display = ['uploaded_by', 'processed', 'created_at', 'processed_at']
    list_filter = ['processed', 'created_at']
    search_fields = ['uploaded_by__username']

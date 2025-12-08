from django.db import models
from django.utils import timezone

# Create your models here.

class Event(models.Model):
    """
    FRC Competition Event
    """
    name = models.CharField(max_length=200)
    event_code = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    
    # API source
    api_source = models.CharField(max_length=20, choices=[('TBA', 'The Blue Alliance'), ('FIRST', 'FIRST API')], default='TBA')
    
    # TBA-specific fields
    tba_event_key = models.CharField(max_length=50, unique=True, null=True, blank=True, help_text="TBA event key (e.g., '2024casj')")
    week = models.IntegerField(null=True, blank=True, help_text="Competition week number")
    event_type = models.IntegerField(null=True, blank=True, help_text="Event type code from TBA")
    event_type_string = models.CharField(max_length=50, blank=True, help_text="Event type (e.g., 'Regional', 'District')")
    
    # Auto-rotation settings for scouter assignment
    auto_rotation_enabled = models.BooleanField(default=False)
    rotation_interval = models.IntegerField(default=5, help_text="Number of matches before rotating scouters")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} ({self.event_code})"


class Team(models.Model):
    """
    FRC Team participating in an event
    """
    team_number = models.IntegerField()
    team_name = models.CharField(max_length=200, blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='teams')
    
    # TBA team information
    nickname = models.CharField(max_length=200, blank=True, help_text="Team nickname from TBA")
    city = models.CharField(max_length=100, blank=True)
    state_prov = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    rookie_year = models.IntegerField(null=True, blank=True)
    
    # Cached external metrics from Statbotics
    epa = models.FloatField(null=True, blank=True, help_text="Expected Points Added")
    win_rate = models.FloatField(null=True, blank=True)
    last_metrics_update = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['team_number', 'event']
        ordering = ['team_number']
    
    def __str__(self):
        return f"Team {self.team_number}"


class Match(models.Model):
    """
    Individual match in a competition
    """
    MATCH_TYPES = [
        ('QUAL', 'Qualification'),
        ('PLAYOFF', 'Playoff'),
    ]
    
    STATUS_CHOICES = [
        ('UPCOMING', 'Upcoming'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('ALL_SUBMITTED', 'All Data Submitted'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='matches')
    match_number = models.IntegerField()
    match_type = models.CharField(max_length=10, choices=MATCH_TYPES, default='QUAL')
    scheduled_time = models.DateTimeField()
    
    # TBA-specific fields
    tba_match_key = models.CharField(max_length=50, unique=True, null=True, blank=True, help_text="TBA match key")
    comp_level = models.CharField(max_length=10, blank=True, help_text="Competition level: qm, qf, sf, f")
    set_number = models.IntegerField(default=1, help_text="Set number for playoff matches")
    actual_time = models.DateTimeField(null=True, blank=True, help_text="Actual match start time")
    predicted_time = models.DateTimeField(null=True, blank=True, help_text="TBA predicted start time")
    
    # Alliance teams (3 per alliance)
    red_1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='red1_matches')
    red_2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='red2_matches')
    red_3 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='red3_matches')
    blue_1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='blue1_matches')
    blue_2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='blue2_matches')
    blue_3 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='blue3_matches')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UPCOMING')
    
    # Actual results
    red_score = models.IntegerField(null=True, blank=True)
    blue_score = models.IntegerField(null=True, blank=True)
    winner = models.CharField(max_length=10, choices=[('RED', 'Red'), ('BLUE', 'Blue'), ('TIE', 'Tie')], null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['event', 'match_number', 'match_type', 'comp_level', 'set_number']
        ordering = ['scheduled_time', 'match_number']
    
    def __str__(self):
        return f"{self.event.event_code} - {self.get_match_type_display()} {self.match_number}"
    
    def get_all_teams(self):
        return [self.red_1, self.red_2, self.red_3, self.blue_1, self.blue_2, self.blue_3]
    
    def check_all_data_submitted(self):
        """Check if all 6 scouters have submitted data"""
        submitted_count = self.scouting_reports.filter(confirmed=True).count()
        if submitted_count >= 6:
            self.status = 'ALL_SUBMITTED'
            self.save()
            return True
        return False

from django.db import models
from django.contrib.auth.models import User
from events.models import Match, Team
from accounts.models import UserProfile

# Create your models here.

class ScouterAssignment(models.Model):
    """
    Assignment of 6 scouters to a match (one per robot)
    """
    POSITION_CHOICES = [
        ('RED_1', 'Red Alliance Position 1'),
        ('RED_2', 'Red Alliance Position 2'),
        ('RED_3', 'Red Alliance Position 3'),
        ('BLUE_1', 'Blue Alliance Position 1'),
        ('BLUE_2', 'Blue Alliance Position 2'),
        ('BLUE_3', 'Blue Alliance Position 3'),
    ]
    
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='assignments')
    scouter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments')
    position = models.CharField(max_length=10, choices=POSITION_CHOICES)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['match', 'position']
        ordering = ['match__scheduled_time', 'position']
    
    def __str__(self):
        return f"{self.scouter.username} -> {self.match} ({self.get_position_display()})"


class MatchPrediction(models.Model):
    """
    Scouter predictions for match outcomes
    """
    scouter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='predictions')
    predicted_winner = models.CharField(max_length=10, choices=[('RED', 'Red'), ('BLUE', 'Blue')])
    
    is_correct = models.BooleanField(null=True, blank=True)
    points_awarded = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['scouter', 'match']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.scouter.username} predicts {self.predicted_winner} for {self.match}"
    
    def check_prediction(self):
        """Check if prediction was correct and award points"""
        if self.match.winner and not self.is_correct:
            self.is_correct = (self.predicted_winner == self.match.winner)
            if self.is_correct:
                self.points_awarded = 1
                self.scouter.profile.add_prediction_point()
            self.save()


class ScoutingReport(models.Model):
    """
    Game-agnostic scouting data collection
    """
    assignment = models.ForeignKey(ScouterAssignment, on_delete=models.CASCADE, related_name='reports')
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='scouting_reports')
    scouter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scouting_reports')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='scouting_reports')
    
    # Pre-Match
    pre_match_notes = models.TextField(blank=True)
    robot_starting_position = models.CharField(max_length=50, blank=True)
    
    # Autonomous Phase
    auto_mobility = models.BooleanField(default=False)
    auto_game_pieces_scored = models.IntegerField(default=0)
    auto_game_pieces_missed = models.IntegerField(default=0)
    auto_points_estimate = models.IntegerField(default=0)
    auto_notes = models.TextField(blank=True)
    
    # Teleoperated Phase
    teleop_game_pieces_scored = models.IntegerField(default=0)
    teleop_game_pieces_missed = models.IntegerField(default=0)
    teleop_defense_rating = models.IntegerField(default=0, help_text="0-5 scale")
    teleop_speed_rating = models.IntegerField(default=0, help_text="0-5 scale")
    teleop_notes = models.TextField(blank=True)
    
    # Endgame Phase
    endgame_climb_attempted = models.BooleanField(default=False)
    endgame_climb_success = models.BooleanField(default=False)
    endgame_park = models.BooleanField(default=False)
    endgame_points_estimate = models.IntegerField(default=0)
    endgame_notes = models.TextField(blank=True)
    
    # Post-Match
    robot_disabled = models.BooleanField(default=False)
    robot_tippy = models.BooleanField(default=False)
    fouls_committed = models.IntegerField(default=0)
    overall_rating = models.IntegerField(default=0, help_text="0-10 scale")
    post_match_notes = models.TextField(blank=True)
    
    # Submission metadata
    submitted_at = models.DateTimeField(auto_now_add=True)
    submitted_offline = models.BooleanField(default=False)
    confirmed = models.BooleanField(default=False)
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_reports')
    
    class Meta:
        unique_together = ['match', 'scouter', 'team']
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.scouter.username} scouting Team {self.team.team_number} in {self.match}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Check if all data submitted
        self.match.check_all_data_submitted()


class QRCodeSubmission(models.Model):
    """
    Offline QR code submissions awaiting processing
    """
    qr_data = models.TextField()
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='qr_uploads')
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        status = "Processed" if self.processed else "Pending"
        return f"QR Upload by {self.uploaded_by.username} - {status}"

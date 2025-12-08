from django.db import models
from events.models import Team, Match

# Create your models here.

class TeamAggregateStats(models.Model):
    """
    Aggregated statistics for a team across all matches
    """
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='aggregate_stats')
    
    # Aggregate auto stats
    avg_auto_game_pieces = models.FloatField(default=0.0)
    avg_auto_points = models.FloatField(default=0.0)
    auto_mobility_rate = models.FloatField(default=0.0)
    
    # Aggregate teleop stats
    avg_teleop_game_pieces = models.FloatField(default=0.0)
    avg_defense_rating = models.FloatField(default=0.0)
    avg_speed_rating = models.FloatField(default=0.0)
    
    # Aggregate endgame stats
    climb_success_rate = models.FloatField(default=0.0)
    avg_endgame_points = models.FloatField(default=0.0)
    
    # Overall metrics
    avg_overall_rating = models.FloatField(default=0.0)
    reliability_score = models.FloatField(default=0.0, help_text="Based on disable/foul rates")
    
    # External metrics from Statbotics
    statbotics_epa = models.FloatField(null=True, blank=True, help_text="Total EPA from Statbotics")
    statbotics_auto_epa = models.FloatField(null=True, blank=True, help_text="Auto EPA from Statbotics")
    statbotics_teleop_epa = models.FloatField(null=True, blank=True, help_text="Teleop EPA from Statbotics")
    statbotics_endgame_epa = models.FloatField(null=True, blank=True, help_text="Endgame EPA from Statbotics")
    statbotics_win_rate = models.FloatField(null=True, blank=True, help_text="Win rate from Statbotics")
    statbotics_rank = models.IntegerField(null=True, blank=True, help_text="Event rank from Statbotics")
    statbotics_last_updated = models.DateTimeField(null=True, blank=True)
    
    matches_scouted = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-avg_overall_rating']
    
    def __str__(self):
        return f"Stats for Team {self.team.team_number}"


class MatchAggregateStats(models.Model):
    """
    Aggregated statistics for a specific match (calculated from all 6 scouting reports)
    """
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name='aggregate_stats')
    
    # Red alliance aggregates
    red_total_auto_points = models.IntegerField(default=0)
    red_total_teleop_points = models.IntegerField(default=0)
    red_total_endgame_points = models.IntegerField(default=0)
    red_predicted_score = models.IntegerField(default=0)
    
    # Blue alliance aggregates
    blue_total_auto_points = models.IntegerField(default=0)
    blue_total_teleop_points = models.IntegerField(default=0)
    blue_total_endgame_points = models.IntegerField(default=0)
    blue_predicted_score = models.IntegerField(default=0)
    
    calculated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Aggregate stats for {self.match}"

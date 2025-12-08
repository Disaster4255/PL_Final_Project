"""
Statbotics API Integration
"""
import statbotics
from django.utils import timezone
from .models import TeamAggregateStats
from events.models import Team


def get_statbotics_client():
    """Get Statbotics API client"""
    return statbotics.Statbotics()


def fetch_team_year_stats(team_number, year):
    """
    Fetch stats for a specific team for a specific year from Statbotics
    Returns: dict with EPA and other metrics
    """
    sb = get_statbotics_client()
    try:
        # Get team year stats
        team_year = sb.get_team_year(team=team_number, year=year)
        
        if team_year:
            # Extract EPA data from nested structure
            epa_data = team_year.get('epa', {})
            epa_breakdown = epa_data.get('breakdown', {})
            total_epa = epa_data.get('total_points', {}).get('mean') if isinstance(epa_data.get('total_points'), dict) else epa_data.get('total_points')
            
            # Extract record data
            record = team_year.get('record', {})
            win_rate = record.get('winrate') if isinstance(record, dict) else None
            
            # Extract rank data
            epa_ranks = epa_data.get('ranks', {})
            total_rank = epa_ranks.get('total', {}).get('rank') if isinstance(epa_ranks.get('total'), dict) else None
            
            return {
                'epa': total_epa,
                'auto_epa': epa_breakdown.get('auto_points'),
                'teleop_epa': epa_breakdown.get('teleop_points'),
                'endgame_epa': epa_breakdown.get('endgame_points'),
                'win_rate': win_rate,
                'rank': total_rank,
            }
    except Exception as e:
        print(f"Error fetching Statbotics data for team {team_number} year {year}: {e}")
        import traceback
        traceback.print_exc()
    
    return None


def fetch_team_event_stats(team_number, event_key):
    """
    Fetch stats for a specific team at a specific event from Statbotics
    Event key format: "2024casj" (year + event code)
    Returns: dict with EPA and other metrics
    """
    sb = get_statbotics_client()
    try:
        # Get team event stats
        team_event = sb.get_team_event(team=team_number, event=event_key)
        
        if team_event:
            # Extract EPA data from nested structure (similar to team_year)
            epa_data = team_event.get('epa', {})
            epa_breakdown = epa_data.get('breakdown', {})
            total_epa = epa_data.get('total_points', {}).get('mean') if isinstance(epa_data.get('total_points'), dict) else epa_data.get('total_points')
            
            # Extract record data
            record = team_event.get('record', {})
            win_rate = record.get('winrate') if isinstance(record, dict) else None
            
            # Rank at event
            rank = team_event.get('rank')
            
            return {
                'epa': total_epa,
                'auto_epa': epa_breakdown.get('auto_points'),
                'teleop_epa': epa_breakdown.get('teleop_points'),
                'endgame_epa': epa_breakdown.get('endgame_points'),
                'win_rate': win_rate,
                'rank': rank,
            }
    except Exception as e:
        print(f"Error fetching Statbotics data for team {team_number} at event {event_key}: {e}")
        import traceback
        traceback.print_exc()
    
    return None


def update_team_aggregate_stats_from_statbotics(team):
    """
    Update TeamAggregateStats with data from Statbotics
    Uses event-specific stats if available, otherwise uses year stats
    """
    event = team.event
    year = event.start_date.year
    
    # Try to get event-specific stats first (if we have TBA event key)
    stats = None
    data_source = None
    if event.tba_event_key:
        stats = fetch_team_event_stats(team.team_number, event.tba_event_key)
        if stats:
            data_source = f"event {event.tba_event_key}"
    
    # Fallback to year stats if event stats not available
    if not stats:
        stats = fetch_team_year_stats(team.team_number, year)
        if stats:
            data_source = f"year {year}"
    
    if not stats:
        print(f"No Statbotics data available for team {team.team_number} (year {year})")
        return None
    
    # Get or create TeamAggregateStats
    team_stats, created = TeamAggregateStats.objects.get_or_create(team=team)
    
    # Update with Statbotics data
    team_stats.statbotics_epa = stats.get('epa')
    team_stats.statbotics_auto_epa = stats.get('auto_epa')
    team_stats.statbotics_teleop_epa = stats.get('teleop_epa')
    team_stats.statbotics_endgame_epa = stats.get('endgame_epa')
    team_stats.statbotics_win_rate = stats.get('win_rate')
    team_stats.statbotics_rank = stats.get('rank')
    team_stats.statbotics_last_updated = timezone.now()
    team_stats.save()
    
    print(f"Updated team {team.team_number} with {data_source} data: EPA={stats.get('epa')}")
    
    return team_stats


def sync_event_statbotics_data(event):
    """
    Sync Statbotics data for all teams in an event
    Returns: number of teams updated
    """
    teams = event.teams.all()
    updated_count = 0
    
    for team in teams:
        result = update_team_aggregate_stats_from_statbotics(team)
        if result:
            updated_count += 1
    
    return updated_count


def get_top_teams_by_epa(event, limit=10):
    """
    Get top teams by EPA for an event
    Returns: QuerySet of TeamAggregateStats ordered by EPA
    """
    return TeamAggregateStats.objects.filter(
        team__event=event,
        statbotics_epa__isnull=False
    ).order_by('-statbotics_epa')[:limit]


def get_combined_ranking(event, limit=None):
    """
    Get teams ranked by a combination of internal scouting data and Statbotics EPA
    This provides a weighted ranking considering both data sources
    Returns: list of (team, combined_score) tuples
    """
    stats = TeamAggregateStats.objects.filter(team__event=event)
    
    rankings = []
    for stat in stats:
        # Normalize scores (0-100 scale)
        internal_score = stat.avg_overall_rating * 10  # Assuming 0-10 scale
        external_score = stat.statbotics_epa if stat.statbotics_epa else 0
        
        # Weight: 60% internal scouting, 40% Statbotics
        # Adjust weights based on data availability
        if stat.matches_scouted > 0 and stat.statbotics_epa:
            combined = (internal_score * 0.6) + (external_score * 0.4)
        elif stat.matches_scouted > 0:
            combined = internal_score
        elif stat.statbotics_epa:
            combined = external_score
        else:
            combined = 0
        
        rankings.append((stat.team, combined))
    
    # Sort by combined score descending
    rankings.sort(key=lambda x: x[1], reverse=True)
    
    if limit:
        return rankings[:limit]
    return rankings

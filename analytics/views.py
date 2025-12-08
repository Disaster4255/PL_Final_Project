from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Avg, Count
from django.utils import timezone
from events.models import Event, Team, Match
from scouting.models import ScoutingReport
from .models import TeamAggregateStats, MatchAggregateStats
from .statbotics_api import get_combined_ranking
import csv
import json

# Create your views here.

@login_required
def dashboard_view(request):
    """Main analytics dashboard"""
    events = Event.objects.all()[:5]
    
    # Get overall statistics
    total_events = Event.objects.count()
    total_teams = Team.objects.count()
    total_reports = ScoutingReport.objects.filter(confirmed=True).count()
    total_matches = Match.objects.count()
    
    # Get recent activity
    recent_reports = ScoutingReport.objects.filter(confirmed=True).select_related('team', 'match', 'scouter').order_by('-submitted_at')[:10]
    
    # Get teams with Statbotics data
    teams_with_epa = TeamAggregateStats.objects.exclude(statbotics_epa__isnull=True).count()
    
    context = {
        'events': events,
        'total_events': total_events,
        'total_teams': total_teams,
        'total_reports': total_reports,
        'total_matches': total_matches,
        'recent_reports': recent_reports,
        'teams_with_epa': teams_with_epa,
    }
    return render(request, 'analytics/dashboard.html', context)

@login_required
def team_stats_view(request, event_id):
    """View team statistics for an event"""
    event = get_object_or_404(Event, id=event_id)
    teams = event.teams.all()
    
    # Calculate aggregate stats
    for team in teams:
        calculate_team_aggregates(team)
    
    stats = TeamAggregateStats.objects.filter(team__event=event).order_by('-avg_overall_rating')
    
    context = {
        'event': event,
        'stats': stats,
    }
    return render(request, 'analytics/team_stats.html', context)

@login_required
def match_analytics_view(request, match_id):
    """View analytics for a specific match"""
    match = get_object_or_404(Match, id=match_id)
    
    # Calculate match aggregates if all data submitted
    if match.status == 'ALL_SUBMITTED':
        calculate_match_aggregates(match)
    
    aggregate = MatchAggregateStats.objects.filter(match=match).first()
    reports = match.scouting_reports.filter(confirmed=True)
    
    context = {
        'match': match,
        'aggregate': aggregate,
        'reports': reports,
    }
    return render(request, 'analytics/match_analytics.html', context)

@login_required
def export_data_view(request, event_id):
    """Export event data to CSV"""
    event = get_object_or_404(Event, id=event_id)
    export_type = request.GET.get('type', 'all')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{event.event_code}_{export_type}.csv"'
    
    writer = csv.writer(response)
    
    if export_type == 'matches':
        # Export match data
        writer.writerow(['Match Number', 'Type', 'Red 1', 'Red 2', 'Red 3', 'Blue 1', 'Blue 2', 'Blue 3', 'Red Score', 'Blue Score', 'Winner', 'Status'])
        for match in event.matches.all():
            writer.writerow([
                match.match_number,
                match.match_type,
                match.red_1.team_number,
                match.red_2.team_number,
                match.red_3.team_number,
                match.blue_1.team_number,
                match.blue_2.team_number,
                match.blue_3.team_number,
                match.red_score or '',
                match.blue_score or '',
                match.winner or '',
                match.status,
            ])
    
    elif export_type == 'scouting':
        # Export scouting reports
        writer.writerow(['Match', 'Team', 'Scouter', 'Auto Points', 'Teleop Scored', 'Endgame Points', 'Overall Rating', 'Confirmed'])
        for report in ScoutingReport.objects.filter(match__event=event, confirmed=True):
            writer.writerow([
                f'{report.match.match_number}',
                report.team.team_number,
                report.scouter.username,
                report.auto_points_estimate,
                report.teleop_game_pieces_scored,
                report.endgame_points_estimate,
                report.overall_rating,
                'Yes' if report.confirmed else 'No',
            ])
    
    elif export_type == 'team_stats':
        # Export team aggregate statistics with EPA values
        writer.writerow([
            'Team', 
            'Nickname',
            'Overall Rating', 
            'Avg Auto Points', 
            'Avg Teleop Pieces', 
            'Climb Success Rate', 
            'Total EPA',
            'Auto EPA',
            'Teleop EPA',
            'Endgame EPA',
            'Win Rate',
            'Matches Scouted'
        ])
        for stat in TeamAggregateStats.objects.filter(team__event=event):
            writer.writerow([
                stat.team.team_number,
                stat.team.nickname or '',
                f'{stat.avg_overall_rating:.1f}' if stat.avg_overall_rating else '0.0',
                f'{stat.avg_auto_points:.1f}' if stat.avg_auto_points else '0.0',
                f'{stat.avg_teleop_game_pieces:.1f}' if stat.avg_teleop_game_pieces else '0.0',
                f'{stat.climb_success_rate:.0f}' if stat.climb_success_rate else '0',
                f'{stat.statbotics_epa:.1f}' if stat.statbotics_epa else '',
                f'{stat.statbotics_auto_epa:.1f}' if stat.statbotics_auto_epa else '',
                f'{stat.statbotics_teleop_epa:.1f}' if stat.statbotics_teleop_epa else '',
                f'{stat.statbotics_endgame_epa:.1f}' if stat.statbotics_endgame_epa else '',
                f'{stat.statbotics_win_rate:.2f}' if stat.statbotics_win_rate else '',
                stat.matches_scouted,
            ])
    
    return response

def calculate_team_aggregates(team):
    """Calculate aggregate statistics for a team"""
    reports = ScoutingReport.objects.filter(team=team, confirmed=True)
    
    if reports.count() == 0:
        return
    
    stats, created = TeamAggregateStats.objects.get_or_create(team=team)
    
    stats.avg_auto_game_pieces = reports.aggregate(Avg('auto_game_pieces_scored'))['auto_game_pieces_scored__avg'] or 0
    stats.avg_auto_points = reports.aggregate(Avg('auto_points_estimate'))['auto_points_estimate__avg'] or 0
    stats.auto_mobility_rate = reports.filter(auto_mobility=True).count() / reports.count() * 100
    
    stats.avg_teleop_game_pieces = reports.aggregate(Avg('teleop_game_pieces_scored'))['teleop_game_pieces_scored__avg'] or 0
    stats.avg_defense_rating = reports.aggregate(Avg('teleop_defense_rating'))['teleop_defense_rating__avg'] or 0
    stats.avg_speed_rating = reports.aggregate(Avg('teleop_speed_rating'))['teleop_speed_rating__avg'] or 0
    
    climb_attempts = reports.filter(endgame_climb_attempted=True).count()
    stats.climb_success_rate = (reports.filter(endgame_climb_success=True).count() / climb_attempts * 100) if climb_attempts > 0 else 0
    stats.avg_endgame_points = reports.aggregate(Avg('endgame_points_estimate'))['endgame_points_estimate__avg'] or 0
    
    stats.avg_overall_rating = reports.aggregate(Avg('overall_rating'))['overall_rating__avg'] or 0
    
    # Reliability score (based on NOT being disabled and low fouls)
    disabled_count = reports.filter(robot_disabled=True).count()
    avg_fouls = reports.aggregate(Avg('fouls_committed'))['fouls_committed__avg'] or 0
    stats.reliability_score = 100 - (disabled_count / reports.count() * 50) - (avg_fouls * 5)
    
    stats.matches_scouted = reports.count()
    stats.save()

def calculate_match_aggregates(match):
    """Calculate aggregate statistics for a match"""
    reports = match.scouting_reports.filter(confirmed=True)
    
    if reports.count() < 6:
        return
    
    aggregate, created = MatchAggregateStats.objects.get_or_create(match=match)
    
    # Red alliance aggregates
    red_teams = [match.red_1, match.red_2, match.red_3]
    red_reports = reports.filter(team__in=red_teams)
    
    aggregate.red_total_auto_points = sum(r.auto_points_estimate for r in red_reports)
    aggregate.red_total_teleop_points = sum(r.teleop_game_pieces_scored * 2 for r in red_reports)  # Assuming 2 pts per piece
    aggregate.red_total_endgame_points = sum(r.endgame_points_estimate for r in red_reports)
    aggregate.red_predicted_score = aggregate.red_total_auto_points + aggregate.red_total_teleop_points + aggregate.red_total_endgame_points
    
    # Blue alliance aggregates
    blue_teams = [match.blue_1, match.blue_2, match.blue_3]
    blue_reports = reports.filter(team__in=blue_teams)
    
    aggregate.blue_total_auto_points = sum(r.auto_points_estimate for r in blue_reports)
    aggregate.blue_total_teleop_points = sum(r.teleop_game_pieces_scored * 2 for r in blue_reports)
    aggregate.blue_total_endgame_points = sum(r.endgame_points_estimate for r in blue_reports)
    aggregate.blue_predicted_score = aggregate.blue_total_auto_points + aggregate.blue_total_teleop_points + aggregate.blue_total_endgame_points
    
    aggregate.save()

@login_required
def fetch_statbotics_data(request, event_id):
    """Fetch and cache Statbotics data for event teams"""
    event = get_object_or_404(Event, id=event_id)
    
    try:
        # Use the real Statbotics API integration
        from .statbotics_api import sync_event_statbotics_data
        updated_count = sync_event_statbotics_data(event)
        
        from django.contrib import messages
        if updated_count > 0:
            messages.success(request, f'Successfully updated Statbotics data for {updated_count} teams')
        else:
            messages.warning(request, 'No Statbotics data available for teams in this event. Data may not exist yet for this season/event.')
    except Exception as e:
        from django.contrib import messages
        messages.error(request, f'Error fetching Statbotics data: {str(e)}')
        import traceback
        traceback.print_exc()
    
    return redirect('team_stats', event_id=event.id)

@login_required
def pick_list_view(request, event_id):
    """Generate pick list for alliance selection using combined ranking"""
    event = get_object_or_404(Event, id=event_id)
    
    # Calculate stats for all teams
    for team in event.teams.all():
        calculate_team_aggregates(team)
    
    # Get combined ranking (internal + Statbotics)
    combined_rankings = get_combined_ranking(event)
    
    # Format for template
    pick_list = []
    for rank, (team, combined_score) in enumerate(combined_rankings, 1):
        # Get stats
        stats = TeamAggregateStats.objects.filter(team=team).first()
        pick_list.append({
            'rank': rank,
            'team': team,
            'combined_score': combined_score,
            'stats': stats,
        })
    
    context = {
        'event': event,
        'pick_list': pick_list,
    }
    return render(request, 'analytics/pick_list.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from accounts.decorators import strategist_or_admin_required
from .models import Event, Team, Match
from .tba_api import import_event_from_tba, import_teams_from_tba, import_matches_from_tba
from analytics.statbotics_api import sync_event_statbotics_data

# Create your views here.

@login_required
def event_list_view(request):
    """List all events"""
    events = Event.objects.all()
    context = {'events': events}
    return render(request, 'events/event_list.html', context)

@strategist_or_admin_required
def create_event_view(request):
    """Create new event and import data from TBA API"""
    if request.method == 'POST':
        tba_event_key = request.POST.get('tba_event_key')
        sync_statbotics = request.POST.get('sync_statbotics') == 'on'
        
        try:
            # Import event from TBA
            event, created = import_event_from_tba(tba_event_key)
            
            if not created:
                messages.warning(request, f'Event {event.name} already exists. Updating data...')
            
            # Import teams
            teams = import_teams_from_tba(event)
            messages.success(request, f'Imported {len(teams)} teams')
            
            # Import matches
            matches = import_matches_from_tba(event)
            messages.success(request, f'Imported {len(matches)} matches')
            
            # Optionally sync Statbotics data
            if sync_statbotics:
                try:
                    updated_count = sync_event_statbotics_data(event)
                    messages.success(request, f'Synced Statbotics data for {updated_count} teams')
                except Exception as e:
                    messages.warning(request, f'Statbotics sync partially failed: {str(e)}')
            
            messages.success(request, f'Event {event.name} imported successfully!')
            return redirect('event_detail', event_id=event.id)
            
        except ValueError as e:
            messages.error(request, f'Configuration error: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error importing event: {str(e)}')
            import traceback
            traceback.print_exc()
    
    return render(request, 'events/create_event.html')

@login_required
def event_detail_view(request, event_id):
    """View event details with matches"""
    event = get_object_or_404(Event, id=event_id)
    matches = event.matches.all()
    teams = event.teams.all()
    
    context = {
        'event': event,
        'matches': matches,
        'teams': teams,
    }
    return render(request, 'events/event_detail.html', context)

@login_required
def match_detail_view(request, match_id):
    """View match details"""
    match = get_object_or_404(Match, id=match_id)
    assignments = match.assignments.all()
    predictions = match.predictions.all()
    reports = match.scouting_reports.filter(confirmed=True)
    
    context = {
        'match': match,
        'assignments': assignments,
        'predictions': predictions,
        'reports': reports,
    }
    return render(request, 'events/match_detail.html', context)

@strategist_or_admin_required
def sync_statbotics_view(request, event_id):
    """Manually trigger Statbotics data sync for an event"""
    event = get_object_or_404(Event, id=event_id)
    
    try:
        updated_count = sync_event_statbotics_data(event)
        messages.success(request, f'Successfully synced Statbotics data for {updated_count} teams')
    except Exception as e:
        messages.error(request, f'Error syncing Statbotics data: {str(e)}')
    
    return redirect('event_detail', event_id=event.id)

@strategist_or_admin_required
def reimport_event_view(request, event_id):
    """Re-import event data from TBA (refresh teams and matches)"""
    event = get_object_or_404(Event, id=event_id)
    
    if not event.tba_event_key:
        messages.error(request, 'This event does not have a TBA event key')
        return redirect('event_detail', event_id=event.id)
    
    try:
        # Re-import teams (will update existing ones)
        teams = import_teams_from_tba(event)
        messages.success(request, f'Re-imported {len(teams)} teams')
        
        # Re-import matches (will update existing ones)
        matches = import_matches_from_tba(event)
        messages.success(request, f'Re-imported {len(matches)} matches')
        
        messages.success(request, f'Event {event.name} re-imported successfully!')
        
    except Exception as e:
        messages.error(request, f'Error re-importing event: {str(e)}')
        import traceback
        traceback.print_exc()
    
    return redirect('event_detail', event_id=event.id)

@strategist_or_admin_required
def reset_matches_view(request, event_id):
    """Reset all matches to UPCOMING status for training/testing purposes"""
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        # Reset all matches to UPCOMING
        matches = event.matches.all()
        updated_count = matches.update(
            status='UPCOMING',
            red_score=None,
            blue_score=None,
            winner=None
        )
        
        # Reset all predictions
        from scouting.models import MatchPrediction
        predictions = MatchPrediction.objects.filter(match__event=event)
        predictions.update(is_correct=None, points_awarded=0)
        
        messages.success(request, f'Reset {updated_count} matches to UPCOMING status')
        messages.info(request, 'All match scores and prediction results have been cleared')
        return redirect('event_detail', event_id=event.id)
    
    # GET request - show confirmation page
    completed_count = event.matches.filter(status='COMPLETED').count()
    context = {
        'event': event,
        'total_matches': event.matches.count(),
        'completed_matches': completed_count,
    }
    return render(request, 'events/confirm_reset_matches.html', context)


@strategist_or_admin_required
def delete_event_view(request, event_id):
    """Delete an event and all related data"""
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        event_name = event.name
        event.delete()  # Cascade delete will handle teams, matches, reports, etc.
        messages.success(request, f'Event "{event_name}" has been deleted')
        return redirect('event_list')
    
    # GET request - show confirmation page
    context = {
        'event': event,
        'teams_count': event.teams.count(),
        'matches_count': event.matches.count(),
    }
    return render(request, 'events/confirm_delete_event.html', context)
"""
The Blue Alliance API Integration
"""
import tbapy
from django.conf import settings
from django.utils import timezone
from datetime import datetime
from .models import Event, Team, Match


def get_tba_client():
    """Get TBA API client with auth key from settings"""
    api_key = getattr(settings, 'TBA_API_KEY', '')
    if not api_key:
        raise ValueError("TBA_API_KEY not configured in settings. Get one from https://www.thebluealliance.com/account")
    return tbapy.TBA(api_key)


def import_event_from_tba(tba_event_key):
    """
    Import event details from TBA
    Returns: Event object
    Raises: ValueError if event key is invalid or event data is incomplete
    """
    # Special case: Generate test data for 2025test
    if tba_event_key == '2025test':
        return _create_test_event()
    
    tba = get_tba_client()
    
    try:
        event_data = tba.event(tba_event_key)
    except Exception as e:
        raise ValueError(f"Invalid TBA event key '{tba_event_key}'. Please check the event key format (e.g., 2025ntwc, 2024casj)")
    
    # Validate required fields
    if not event_data:
        raise ValueError(f"Event '{tba_event_key}' not found in The Blue Alliance")
    
    if 'start_date' not in event_data or 'end_date' not in event_data:
        raise ValueError(f"Event '{tba_event_key}' exists but is missing required date information. It may be an invalid or future event.")
    
    if 'name' not in event_data:
        raise ValueError(f"Event '{tba_event_key}' data is incomplete")
    
    # Create or update event
    event, created = Event.objects.update_or_create(
        tba_event_key=tba_event_key,
        defaults={
            'name': event_data.get('name', ''),
            'event_code': event_data.get('event_code', tba_event_key),
            'location': f"{event_data.get('city', '')}, {event_data.get('state_prov', '')}, {event_data.get('country', '')}",
            'start_date': datetime.strptime(event_data['start_date'], '%Y-%m-%d').date(),
            'end_date': datetime.strptime(event_data['end_date'], '%Y-%m-%d').date(),
            'week': event_data.get('week'),
            'event_type': event_data.get('event_type'),
            'event_type_string': event_data.get('event_type_string', ''),
            'api_source': 'TBA',
        }
    )
    
    return event, created


def _create_test_event():
    """
    Create a test event with sample data for testing purposes
    Event key: 2025test
    """
    from django.utils import timezone
    from datetime import timedelta
    
    # Create test event
    today = timezone.now().date()
    event, created = Event.objects.update_or_create(
        tba_event_key='2025test',
        defaults={
            'name': 'Test Competition 2025',
            'event_code': 'test',
            'location': 'Test City, CA, USA',
            'start_date': today,
            'end_date': today + timedelta(days=2),
            'week': 1,
            'event_type': 0,
            'event_type_string': 'Regional',
            'api_source': 'Test Data',
        }
    )
    
    # Create 12 test teams
    test_teams = [
        (254, 'The Cheesy Poofs', 'San Jose', 'CA', 'USA'),
        (1678, 'Citrus Circuits', 'Davis', 'CA', 'USA'),
        (971, 'Spartan Robotics', 'Mountain View', 'CA', 'USA'),
        (2056, 'OP Robotics', 'Fremont', 'CA', 'USA'),
        (604, 'Quixilver', 'Fremont', 'CA', 'USA'),
        (1323, 'MadTown Robotics', 'Madison', 'WI', 'USA'),
        (118, 'Robonauts', 'Houston', 'TX', 'USA'),
        (148, 'Robowranglers', 'Greenville', 'TX', 'USA'),
        (3476, 'Code Orange', 'Orange', 'CA', 'USA'),
        (2910, 'Jack in the Bot', 'San Diego', 'CA', 'USA'),
        (2485, 'W.A.R. Lords', 'San Jose', 'CA', 'USA'),
        (1138, 'Eagle Robotics', 'San Jose', 'CA', 'USA'),
    ]
    
    imported_teams = []
    for team_num, nickname, city, state, country in test_teams:
        team, _ = Team.objects.update_or_create(
            team_number=team_num,
            event=event,
            defaults={
                'team_name': f'Team {team_num}',
                'nickname': nickname,
                'city': city,
                'state_prov': state,
                'country': country,
                'rookie_year': 2000,
            }
        )
        imported_teams.append(team)
    
    # Create 12 qualification matches
    match_time = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time().replace(hour=9)))
    
    for match_num in range(1, 13):
        # Rotate teams through matches
        red_teams = [imported_teams[(match_num * 3) % 12], 
                     imported_teams[(match_num * 3 + 1) % 12], 
                     imported_teams[(match_num * 3 + 2) % 12]]
        blue_teams = [imported_teams[(match_num * 3 + 3) % 12], 
                      imported_teams[(match_num * 3 + 4) % 12], 
                      imported_teams[(match_num * 3 + 5) % 12]]
        
        Match.objects.update_or_create(
            event=event,
            match_number=match_num,
            match_type='QUAL',
            comp_level='qm',
            set_number=1,
            defaults={
                'tba_match_key': f'2025test_qm{match_num}',
                'scheduled_time': match_time + timedelta(minutes=(match_num - 1) * 10),
                'red_1': red_teams[0],
                'red_2': red_teams[1],
                'red_3': red_teams[2],
                'blue_1': blue_teams[0],
                'blue_2': blue_teams[1],
                'blue_3': blue_teams[2],
                'status': 'UPCOMING',
            }
        )
    
    return event, created


def import_teams_from_tba(event):
    """
    Import all teams participating in an event from TBA
    Returns: list of Team objects
    """
    if not event.tba_event_key:
        raise ValueError("Event must have a TBA event key")
    
    tba = get_tba_client()
    teams_data = tba.event_teams(event.tba_event_key)
    
    imported_teams = []
    for team_data in teams_data:
        team, created = Team.objects.update_or_create(
            team_number=team_data['team_number'],
            event=event,
            defaults={
                'team_name': team_data.get('name', ''),
                'nickname': team_data.get('nickname', ''),
                'city': team_data.get('city', ''),
                'state_prov': team_data.get('state_prov', ''),
                'country': team_data.get('country', ''),
                'rookie_year': team_data.get('rookie_year'),
            }
        )
        imported_teams.append(team)
    
    return imported_teams


def import_matches_from_tba(event):
    """
    Import all matches for an event from TBA
    Returns: list of Match objects
    """
    if not event.tba_event_key:
        raise ValueError("Event must have a TBA event key")
    
    tba = get_tba_client()
    matches_data = tba.event_matches(event.tba_event_key)
    
    imported_matches = []
    for match_data in matches_data:
        try:
            # Parse alliances
            red_teams = match_data['alliances']['red']['team_keys']
            blue_teams = match_data['alliances']['blue']['team_keys']
            
            # Extract team numbers from keys (e.g., 'frc254' -> 254)
            red_numbers = [int(key.replace('frc', '')) for key in red_teams]
            blue_numbers = [int(key.replace('frc', '')) for key in blue_teams]
            
            # Get team objects
            try:
                red_1 = Team.objects.get(team_number=red_numbers[0], event=event)
                red_2 = Team.objects.get(team_number=red_numbers[1], event=event)
                red_3 = Team.objects.get(team_number=red_numbers[2], event=event)
                blue_1 = Team.objects.get(team_number=blue_numbers[0], event=event)
                blue_2 = Team.objects.get(team_number=blue_numbers[1], event=event)
                blue_3 = Team.objects.get(team_number=blue_numbers[2], event=event)
            except Team.DoesNotExist as e:
                # Skip matches with teams not in database
                print(f"Skipping match {match_data.get('key')}: Team not found - {str(e)}")
                continue
        
            # Determine match type
            comp_level = match_data['comp_level']
            match_type = 'PLAYOFF' if comp_level in ['qf', 'sf', 'f'] else 'QUAL'
            
            # Parse times
            scheduled_time = None
            if match_data.get('time'):
                scheduled_time = timezone.make_aware(datetime.fromtimestamp(match_data['time']))
            elif match_data.get('predicted_time'):
                scheduled_time = timezone.make_aware(datetime.fromtimestamp(match_data['predicted_time']))
            else:
                # Default to event start date at noon if no time available
                scheduled_time = timezone.make_aware(datetime.combine(event.start_date, datetime.min.time().replace(hour=12)))
            
            actual_time = None
            if match_data.get('actual_time'):
                actual_time = timezone.make_aware(datetime.fromtimestamp(match_data['actual_time']))
            
            predicted_time = None
            if match_data.get('predicted_time'):
                predicted_time = timezone.make_aware(datetime.fromtimestamp(match_data['predicted_time']))
            
            # Determine winner and scores
            red_score = match_data['alliances']['red'].get('score')
            blue_score = match_data['alliances']['blue'].get('score')
            
            winner = None
            status = 'UPCOMING'
            if red_score is not None and blue_score is not None:
                if red_score > blue_score:
                    winner = 'RED'
                elif blue_score > red_score:
                    winner = 'BLUE'
                else:
                    winner = 'TIE'
                status = 'COMPLETED'
            
            # Create or update match
            match, created = Match.objects.update_or_create(
                tba_match_key=match_data['key'],
                defaults={
                    'event': event,
                    'match_number': match_data['match_number'],
                    'match_type': match_type,
                    'comp_level': comp_level,
                    'set_number': match_data.get('set_number', 1),
                    'scheduled_time': scheduled_time,
                    'actual_time': actual_time,
                    'predicted_time': predicted_time,
                    'red_1': red_1,
                    'red_2': red_2,
                    'red_3': red_3,
                    'blue_1': blue_1,
                    'blue_2': blue_2,
                    'blue_3': blue_3,
                    'red_score': red_score,
                    'blue_score': blue_score,
                    'winner': winner,
                    'status': status,
                }
            )
            imported_matches.append(match)
        except Exception as e:
            print(f"Error importing match {match_data.get('key', 'unknown')}: {str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    return imported_matches


def get_event_oprs(event):
    """
    Get OPR (Offensive Power Rating), DPR, and CCWM for all teams at an event
    Returns: dict with team_key as key and dict of stats as value
    """
    if not event.tba_event_key:
        raise ValueError("Event must have a TBA event key")
    
    tba = get_tba_client()
    try:
        oprs = tba.event_oprs(event.tba_event_key)
        return oprs
    except Exception as e:
        print(f"Error fetching OPRs: {e}")
        return None

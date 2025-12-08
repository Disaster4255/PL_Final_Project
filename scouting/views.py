from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from accounts.decorators import strategist_or_admin_required, scouter_required
from .models import ScouterAssignment, MatchPrediction, ScoutingReport, QRCodeSubmission
from events.models import Match, Team
import json
import base64
import random
import io

# Create your views here.

@scouter_required
def scouter_dashboard_view(request):
    """Dashboard showing scouter's assignments"""
    user = request.user
    # Filter by match status instead of time - matches can be delayed
    upcoming_assignments = ScouterAssignment.objects.filter(
        scouter=user,
        match__status__in=['UPCOMING', 'IN_PROGRESS']
    ).select_related('match', 'team').order_by('match__scheduled_time')[:10]
    
    recent_reports = ScoutingReport.objects.filter(
        scouter=user
    ).select_related('match', 'team').order_by('-submitted_at')[:5]
    
    context = {
        'upcoming_assignments': upcoming_assignments,
        'recent_reports': recent_reports,
    }
    return render(request, 'scouting/scouter_dashboard.html', context)

@strategist_or_admin_required
def assign_scouters_view(request, match_id):
    """Manually assign scouters to a match"""
    match = get_object_or_404(Match, id=match_id)
    scouters = User.objects.filter(profile__role='SCOUTER')
    
    if request.method == 'POST':
        # Clear existing assignments
        match.assignments.all().delete()
        
        # Get all teams in the match
        teams = [match.red_1, match.red_2, match.red_3, match.blue_1, match.blue_2, match.blue_3]
        positions = ['RED_1', 'RED_2', 'RED_3', 'BLUE_1', 'BLUE_2', 'BLUE_3']
        
        # Create new assignments
        for i, (team, position) in enumerate(zip(teams, positions)):
            scouter_id = request.POST.get(f'scouter_{i}')
            if scouter_id:
                scouter = User.objects.get(id=scouter_id)
                ScouterAssignment.objects.create(
                    match=match,
                    scouter=scouter,
                    position=position,
                    team=team
                )
        
        messages.success(request, 'Scouters assigned successfully')
        return redirect('match_detail', match_id=match.id)
    
    context = {
        'match': match,
        'scouters': scouters,
        'teams': [match.red_1, match.red_2, match.red_3, match.blue_1, match.blue_2, match.blue_3],
    }
    return render(request, 'scouting/assign_scouters.html', context)

@strategist_or_admin_required
def auto_assign_scouters_view(request, event_id):
    """Automatically assign scouters to all matches in an event"""
    from events.models import Event
    
    event = get_object_or_404(Event, id=event_id)
    scouters = list(User.objects.filter(profile__role='SCOUTER'))
    
    if len(scouters) < 6:
        messages.error(request, 'Need at least 6 scouters for auto-assignment')
        return redirect('event_detail', event_id=event.id)
    
    matches = event.matches.filter(status='UPCOMING').order_by('scheduled_time')
    rotation_interval = event.rotation_interval
    
    current_rotation = random.sample(scouters, 6)
    match_count = 0
    
    for match in matches:
        # Clear existing assignments
        match.assignments.all().delete()
        
        # Rotate scouters if needed
        if match_count > 0 and match_count % rotation_interval == 0:
            current_rotation = random.sample(scouters, 6)
        
        teams = [match.red_1, match.red_2, match.red_3, match.blue_1, match.blue_2, match.blue_3]
        positions = ['RED_1', 'RED_2', 'RED_3', 'BLUE_1', 'BLUE_2', 'BLUE_3']
        
        for scouter, team, position in zip(current_rotation, teams, positions):
            ScouterAssignment.objects.create(
                match=match,
                scouter=scouter,
                position=position,
                team=team
            )
        
        match_count += 1
    
    messages.success(request, f'Auto-assigned scouters to {match_count} matches')
    return redirect('event_detail', event_id=event.id)

@scouter_required
def submit_scouting_report_view(request, assignment_id):
    """Submit scouting data for an assignment"""
    assignment = get_object_or_404(ScouterAssignment, id=assignment_id)
    
    # Check if user is the assigned scouter
    if assignment.scouter != request.user:
        messages.error(request, 'You are not assigned to this match')
        return redirect('scouter_dashboard')
    
    # Check if report already exists for this assignment
    existing_report = ScoutingReport.objects.filter(
        assignment=assignment,
        match=assignment.match,
        scouter=request.user,
        team=assignment.team
    ).first()
    
    if existing_report:
        messages.info(request, f'Report already submitted for this assignment. You can edit it if needed.')
        context = {
            'assignment': assignment,
            'existing_report': existing_report,
        }
        return render(request, 'scouting/submit_report.html', context)
    
    if request.method == 'POST':
        # Double-check to prevent race conditions
        existing_report = ScoutingReport.objects.filter(
            assignment=assignment,
            match=assignment.match,
            scouter=request.user,
            team=assignment.team
        ).first()
        
        if existing_report:
            messages.warning(request, 'Report was already submitted (duplicate prevented)')
            return redirect('scouter_dashboard')
        
        # Create scouting report
        try:
            report = ScoutingReport.objects.create(
            assignment=assignment,
            match=assignment.match,
            scouter=request.user,
            team=assignment.team,
            # Pre-Match
            pre_match_notes=request.POST.get('pre_match_notes', ''),
            robot_starting_position=request.POST.get('robot_starting_position', ''),
            # Autonomous
            auto_mobility=request.POST.get('auto_mobility') == 'on',
            auto_game_pieces_scored=int(request.POST.get('auto_game_pieces_scored', 0)),
            auto_game_pieces_missed=int(request.POST.get('auto_game_pieces_missed', 0)),
            auto_points_estimate=int(request.POST.get('auto_points_estimate', 0)),
            auto_notes=request.POST.get('auto_notes', ''),
            # Teleoperated
            teleop_game_pieces_scored=int(request.POST.get('teleop_game_pieces_scored', 0)),
            teleop_game_pieces_missed=int(request.POST.get('teleop_game_pieces_missed', 0)),
            teleop_defense_rating=int(request.POST.get('teleop_defense_rating', 0)),
            teleop_speed_rating=int(request.POST.get('teleop_speed_rating', 0)),
            teleop_notes=request.POST.get('teleop_notes', ''),
            # Endgame
            endgame_climb_attempted=request.POST.get('endgame_climb_attempted') == 'on',
            endgame_climb_success=request.POST.get('endgame_climb_success') == 'on',
            endgame_park=request.POST.get('endgame_park') == 'on',
            endgame_points_estimate=int(request.POST.get('endgame_points_estimate', 0)),
            endgame_notes=request.POST.get('endgame_notes', ''),
            # Post-Match
            robot_disabled=request.POST.get('robot_disabled') == 'on',
            robot_tippy=request.POST.get('robot_tippy') == 'on',
            fouls_committed=int(request.POST.get('fouls_committed', 0)),
            overall_rating=int(request.POST.get('overall_rating', 5)),
            post_match_notes=request.POST.get('post_match_notes', ''),
            submitted_offline=request.POST.get('offline_mode') == 'true',
            confirmed=False
        )
        
            # Check if offline submission
            if report.submitted_offline:
                # Generate QR code
                return generate_qr_code_view(request, report.id)
            else:
                messages.success(request, 'Scouting report submitted successfully')
                return redirect('scouter_dashboard')
        
        except Exception as e:
            messages.error(request, f'Error submitting report: {str(e)}')
            # Log the error for debugging
            import traceback
            traceback.print_exc()
    
    context = {
        'assignment': assignment,
        'existing_report': None,
    }
    return render(request, 'scouting/submit_report.html', context)

@scouter_required
def submit_prediction_view(request, match_id):
    """Submit match prediction"""
    match = get_object_or_404(Match, id=match_id)
    
    # Check for existing prediction
    existing_prediction = MatchPrediction.objects.filter(
        scouter=request.user,
        match=match
    ).first()
    
    if request.method == 'POST':
        predicted_winner = request.POST.get('predicted_winner')
        
        if not predicted_winner:
            messages.error(request, 'Please select a predicted winner')
            context = {
                'match': match,
                'existing_prediction': existing_prediction
            }
            return render(request, 'scouting/submit_prediction.html', context)
        
        try:
            # Create or update prediction (get_or_create handles race conditions)
            prediction, created = MatchPrediction.objects.get_or_create(
                scouter=request.user,
                match=match,
                defaults={'predicted_winner': predicted_winner}
            )
            
            if not created:
                # Update existing prediction if match hasn't started
                if match.status == 'UPCOMING':
                    old_prediction = prediction.predicted_winner
                    prediction.predicted_winner = predicted_winner
                    prediction.save()
                    messages.success(request, f'Prediction updated from {old_prediction} to {predicted_winner}')
                else:
                    messages.warning(request, 'Cannot change prediction - match has already started')
            else:
                messages.success(request, 'Prediction submitted successfully')
                
        except Exception as e:
            messages.error(request, f'Error submitting prediction: {str(e)}')
            import traceback
            traceback.print_exc()
        
        return redirect('match_detail', match_id=match.id)
    
    context = {
        'match': match,
        'existing_prediction': existing_prediction
    }
    return render(request, 'scouting/submit_prediction.html', context)

def generate_qr_code_svg(data_string):
    """
    Generate a simple QR code as SVG using pure Python.
    This is a simplified version suitable for educational purposes.
    For production, use a proper QR library.
    """
    # For simplicity, create a data matrix representation
    # In a real QR code, this would include error correction, masking, etc.
    
    # Create a simple grid pattern based on the data
    # Each character contributes to the pattern
    size = 25  # 25x25 grid
    cell_size = 10  # pixels per cell
    
    # Initialize grid
    grid = [[0 for _ in range(size)] for _ in range(size)]
    
    # Add finder patterns (corners)
    for i in range(7):
        for j in range(7):
            if (i == 0 or i == 6 or j == 0 or j == 6 or (i >= 2 and i <= 4 and j >= 2 and j <= 4)):
                grid[i][j] = 1
                grid[i][size-1-j] = 1
                grid[size-1-i][j] = 1
    
    # Encode data into grid (simple hash-based pattern)
    for idx, char in enumerate(data_string):
        hash_val = hash(char + str(idx))
        row = (abs(hash_val) % (size - 8)) + 7
        col = (abs(hash_val * 7) % (size - 8)) + 7
        if row < size and col < size:
            grid[row][col] = ord(char) % 2
    
    # Generate SVG
    svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size*cell_size} {size*cell_size}" width="300" height="300">']
    svg_parts.append(f'<rect width="{size*cell_size}" height="{size*cell_size}" fill="white"/>')
    
    for row in range(size):
        for col in range(size):
            if grid[row][col]:
                x = col * cell_size
                y = row * cell_size
                svg_parts.append(f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="black"/>')
    
    svg_parts.append('</svg>')
    return ''.join(svg_parts)


def generate_qr_code_view(request, report_id):
    """Generate QR code for offline submission"""
    report = get_object_or_404(ScoutingReport, id=report_id)
    
    # Serialize report data
    data = {
        'report_id': report.id,
        'match_id': report.match.id,
        'team_number': report.team.team_number,
        'scouter': report.scouter.username,
        'pre_match_notes': report.pre_match_notes,
        'robot_starting_position': report.robot_starting_position,
        'auto_mobility': report.auto_mobility,
        'auto_game_pieces_scored': report.auto_game_pieces_scored,
        'auto_game_pieces_missed': report.auto_game_pieces_missed,
        'auto_points_estimate': report.auto_points_estimate,
        'auto_notes': report.auto_notes,
        'teleop_game_pieces_scored': report.teleop_game_pieces_scored,
        'teleop_game_pieces_missed': report.teleop_game_pieces_missed,
        'teleop_defense_rating': report.teleop_defense_rating,
        'teleop_speed_rating': report.teleop_speed_rating,
        'teleop_notes': report.teleop_notes,
        'endgame_climb_attempted': report.endgame_climb_attempted,
        'endgame_climb_success': report.endgame_climb_success,
        'endgame_park': report.endgame_park,
        'endgame_points_estimate': report.endgame_points_estimate,
        'endgame_notes': report.endgame_notes,
        'robot_disabled': report.robot_disabled,
        'robot_tippy': report.robot_tippy,
        'fouls_committed': report.fouls_committed,
        'overall_rating': report.overall_rating,
        'post_match_notes': report.post_match_notes,
    }
    
    # Convert to JSON and base64
    json_data = json.dumps(data)
    qr_data = base64.b64encode(json_data.encode()).decode()
    
    # Generate QR code SVG
    qr_svg = generate_qr_code_svg(qr_data[:100])  # Use first 100 chars for pattern
    
    context = {
        'qr_data': qr_data,
        'qr_svg': qr_svg,
        'report': report,
        'data_size': len(qr_data),
    }
    return render(request, 'scouting/qr_code.html', context)

@strategist_or_admin_required
def scan_qr_code_view(request):
    """Scan and process QR code submissions"""
    if request.method == 'POST':
        qr_data = request.POST.get('qr_data', '').strip()
        
        if not qr_data:
            messages.error(request, 'No QR code data provided')
            return render(request, 'scouting/scan_qr.html')
        
        try:
            # Decode QR data
            json_data = base64.b64decode(qr_data.encode()).decode()
            data = json.loads(json_data)
            
            # Validate required fields
            required_fields = ['match_id', 'team_number', 'scouter']
            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                messages.error(request, f'Missing required fields: {", ".join(missing_fields)}')
                return render(request, 'scouting/scan_qr.html')
            
            # Find match and team
            match = Match.objects.get(id=data['match_id'])
            team = Team.objects.get(team_number=data['team_number'], event=match.event)
            scouter = User.objects.get(username=data['scouter'])
            assignment = ScouterAssignment.objects.get(match=match, scouter=scouter, team=team)
            
            # Check for existing report (duplicate detection)
            existing_report = ScoutingReport.objects.filter(
                assignment=assignment,
                match=match,
                scouter=scouter,
                team=team
            ).first()
            
            if existing_report:
                # Check if this is the same report (already scanned)
                if 'report_id' in data and existing_report.id == data['report_id']:
                    messages.warning(request, f'This QR code has already been scanned (Report #{existing_report.id})')
                    return redirect('view_match_reports', match_id=match.id)
                else:
                    messages.error(request, f'Scouter {scouter.username} already has a report for this match/team')
                    return render(request, 'scouting/scan_qr.html')
            
            # Create scouting report
            report = ScoutingReport.objects.create(
                assignment=assignment,
                match=match,
                scouter=scouter,
                team=team,
                pre_match_notes=data.get('pre_match_notes', ''),
                robot_starting_position=data.get('robot_starting_position', ''),
                auto_mobility=data.get('auto_mobility', False),
                auto_game_pieces_scored=data.get('auto_game_pieces_scored', 0),
                auto_game_pieces_missed=data.get('auto_game_pieces_missed', 0),
                auto_points_estimate=data.get('auto_points_estimate', 0),
                auto_notes=data.get('auto_notes', ''),
                teleop_game_pieces_scored=data.get('teleop_game_pieces_scored', 0),
                teleop_game_pieces_missed=data.get('teleop_game_pieces_missed', 0),
                teleop_defense_rating=data.get('teleop_defense_rating', 0),
                teleop_speed_rating=data.get('teleop_speed_rating', 0),
                teleop_notes=data.get('teleop_notes', ''),
                endgame_climb_attempted=data.get('endgame_climb_attempted', False),
                endgame_climb_success=data.get('endgame_climb_success', False),
                endgame_park=data.get('endgame_park', False),
                endgame_points_estimate=data.get('endgame_points_estimate', 0),
                endgame_notes=data.get('endgame_notes', ''),
                robot_disabled=data.get('robot_disabled', False),
                robot_tippy=data.get('robot_tippy', False),
                fouls_committed=data.get('fouls_committed', 0),
                overall_rating=data.get('overall_rating', 5),
                post_match_notes=data.get('post_match_notes', ''),
                submitted_offline=True,
                confirmed=False
            )
            
            messages.success(request, f'✓ QR code processed successfully')
            messages.info(request, f'Report from {scouter.username} for Team {team.team_number} in Match {match.match_number}')
            return redirect('view_match_reports', match_id=match.id)
            
        except base64.binascii.Error:
            messages.error(request, 'Invalid QR code format (not valid base64)')
        except json.JSONDecodeError:
            messages.error(request, 'Invalid QR code data (not valid JSON)')
        except Match.DoesNotExist:
            messages.error(request, f'Match not found (ID: {data.get("match_id", "unknown")})')
        except Team.DoesNotExist:
            messages.error(request, f'Team {data.get("team_number", "unknown")} not found in this event')
        except User.DoesNotExist:
            messages.error(request, f'Scouter "{data.get("scouter", "unknown")}" not found')
        except ScouterAssignment.DoesNotExist:
            messages.error(request, f'No assignment found for this scouter/match/team combination')
        except Exception as e:
            messages.error(request, f'Error processing QR code: {str(e)}')
            import traceback
            traceback.print_exc()
    
    return render(request, 'scouting/scan_qr.html')

@strategist_or_admin_required
def confirm_report_view(request, report_id):
    """Confirm a scouting report and award XP"""
    report = get_object_or_404(ScoutingReport, id=report_id)
    
    if not report.confirmed:
        report.confirmed = True
        report.confirmed_by = request.user
        report.save()
        # Award XP for confirmed report
        report.scouter.profile.add_experience(10)
        messages.success(request, f'Report confirmed. Awarded 10 XP to {report.scouter.username}')
    else:
        messages.info(request, 'Report was already confirmed')
    
    return redirect('match_detail', match_id=report.match.id)

@strategist_or_admin_required
def view_match_reports_view(request, match_id):
    """View all scouting reports for a match (strategist/admin only)"""
    match = get_object_or_404(Match, id=match_id)
    reports = match.scouting_reports.all().select_related('scouter', 'team', 'assignment')
    assignments = match.assignments.all().select_related('scouter', 'team')
    predictions = match.predictions.all().select_related('scouter')
    
    # Calculate submission status
    total_assignments = assignments.count()
    confirmed_reports = reports.filter(confirmed=True).count()
    pending_reports = reports.filter(confirmed=False).count()
    missing_reports = total_assignments - reports.count()
    
    context = {
        'match': match,
        'reports': reports,
        'assignments': assignments,
        'predictions': predictions,
        'total_assignments': total_assignments,
        'confirmed_reports': confirmed_reports,
        'pending_reports': pending_reports,
        'missing_reports': missing_reports,
    }
    return render(request, 'scouting/view_match_reports.html', context)


@strategist_or_admin_required
def complete_match_view(request, match_id):
    """Mark match as complete, verify predictions, and update XP"""
    match = get_object_or_404(Match, id=match_id)
    
    if request.method == 'POST':
        # Get match results
        red_score = request.POST.get('red_score')
        blue_score = request.POST.get('blue_score')
        
        if red_score and blue_score:
            try:
                red_score = int(red_score)
                blue_score = int(blue_score)
                
                # Update match status and scores
                match.red_score = red_score
                match.blue_score = blue_score
                
                # Determine winner
                if red_score > blue_score:
                    match.winner = 'RED'
                elif blue_score > red_score:
                    match.winner = 'BLUE'
                else:
                    match.winner = 'TIE'
                
                match.status = 'COMPLETED'
                match.save()
                
                # Verify all predictions for this match
                predictions = match.predictions.all()
                correct_count = 0
                for prediction in predictions:
                    prediction.check_prediction()
                    if prediction.is_correct:
                        correct_count += 1
                
                # Award bonus XP to scouters who submitted reports
                confirmed_reports = match.scouting_reports.filter(confirmed=True)
                for report in confirmed_reports:
                    report.scouter.profile.add_experience(5)  # Bonus XP for match completion
                
                messages.success(request, f'Match marked as complete. {match.winner} alliance wins {max(red_score, blue_score)}-{min(red_score, blue_score)}')
                messages.success(request, f'Verified {predictions.count()} predictions ({correct_count} correct)')
                messages.success(request, f'Awarded bonus XP to {confirmed_reports.count()} scouters')
                
                return redirect('match_detail', match_id=match.id)
                
            except ValueError:
                messages.error(request, 'Invalid score values')
        else:
            messages.error(request, 'Both red and blue scores are required')
    
    # GET request - show form
    reports = match.scouting_reports.filter(confirmed=True).select_related('scouter', 'team')
    predictions = match.predictions.all().select_related('scouter')
    
    context = {
        'match': match,
        'reports': reports,
        'predictions': predictions,
    }
    return render(request, 'scouting/complete_match.html', context)


@login_required
def prediction_leaderboard_view(request):
    """View prediction leaderboard"""
    from accounts.models import UserProfile
    
    leaderboard = UserProfile.objects.filter(role='SCOUTER').order_by('-prediction_points')
    
    context = {'leaderboard': leaderboard}
    return render(request, 'scouting/leaderboard.html', context)

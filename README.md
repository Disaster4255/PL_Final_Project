# FRC Scouting App

A Django web application for FRC (FIRST Robotics Competition) scouting and team analysis.

## Features

- Event and match management via The Blue Alliance API
- Real-time team statistics from Statbotics
- Match scouting with detailed reports (auto, teleop, endgame)
- Match predictions with XP rewards
- Offline QR code submission support
- Pick list generation with combined analytics
- User roles: Admin, Strategist, Scouter
- Gamified XP and leveling system

## Quick Setup

### 1. Install Dependencies

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file in project root:
```
TBA_API_KEY=your_tba_api_key_here
```

Get your TBA API key: https://www.thebluealliance.com/account

### 3. Initialize Database

```bash
python manage.py migrate
python manage.py createsuperuser
python setup_admin.py  # Optional: Create test users
```

### 4. Run Server

```bash
python manage.py runserver
```

Visit: http://localhost:8000

## Usage

1. **Import Event**: Create event with TBA event key (e.g., "2024mrcmp")
2. **Assign Scouters**: Auto-assign or manually assign to matches
3. **Submit Reports**: Scouters fill out match observations
4. **Predict Matches**: Make predictions before matches start
5. **Generate QR Codes**: For offline submissions
6. **Complete Matches**: Mark matches complete and verify predictions
7. **View Analytics**: Team stats, EPA data, and pick lists

## Project Structure

```
frc_scouting/     # Django settings
accounts/         # User authentication and profiles
analytics/        # Statbotics integration and analytics
events/           # Event and match management
scouting/         # Scouting reports and predictions
templates/        # HTML templates
```

## Tech Stack

- Django 6.0
- SQLite database
- The Blue Alliance API (tbapy 1.3.2)
- Statbotics API (statbotics 3.0.0)
- Python standard library (no external dependencies for QR codes)

## Production Deployment

For production deployment:
1. Set `DEBUG=False` in settings
2. Configure proper `SECRET_KEY`
3. Use PostgreSQL instead of SQLite
4. Set up proper static file serving
5. Configure ALLOWED_HOSTS
6. Use environment variables for sensitive data

## License

MIT License

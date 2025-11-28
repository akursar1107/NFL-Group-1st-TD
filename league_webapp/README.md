# NFL First TD League Web App

A Flask-based web application for managing an NFL First Touchdown betting league with bankroll tracking, pick management, and automated grading.

## Features

- **User Management**: Track multiple league members with individual bankrolls
- **Weekly Pick Submission**: Select first TD scorer picks with real-time odds
- **Automated Grading**: Score picks against actual game results
- **Bankroll Tracking**: Monitor winnings/losses over the season
- **NFL Data Integration**: Uses shared `nfl_core` package for statistics and odds

## Prerequisites

- Python 3.10 or higher
- Virtual environment (recommended)
- API key from [The Odds API](https://the-odds-api.com/) (optional, for live odds)

## Installation

1. **Navigate to main directory**:
   ```bash
   cd main
   ```

2. **Create and activate virtual environment** (if not already done):
   ```powershell
   # Windows PowerShell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   ```bash
   # Mac/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install the shared nfl_core package**:
   ```bash
   pip install -e nfl_core
   ```

4. **Install webapp dependencies**:
   ```bash
   pip install -r league_webapp/requirements.txt
   ```

5. **Configure environment variables**:
   Create a `.env` file in the `league_webapp` directory:
   ```
   SECRET_KEY=your-secret-key-here
   ODDS_API_KEY=your-odds-api-key-here
   ```

6. **Initialize database**:
   ```bash
   cd league_webapp
   python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
   ```

## Usage

1. **Start the application**:
   ```bash
   cd league_webapp
   python run.py
   ```

2. **Access the web interface**:
   Open your browser to `http://localhost:5000`

3. **Initial Setup**:
   - Add users through the admin interface
   - Set starting bankrolls for each user
   - Import game schedule for the current week

## Project Structure

```
league_webapp/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # Database models (User, Game, Pick, Bankroll)
│   ├── routes.py            # Web routes and views
│   ├── data_loader.py       # NFL data loading utilities
│   ├── templates/           # Jinja2 HTML templates
│   └── static/              # CSS, JS, images
├── scripts/
│   └── setup/               # Database setup scripts
├── instance/                # SQLite database (auto-created)
├── auto_grade.py            # Automated weekly grading
├── grade_week.py            # Manual grading utility
├── run.py                   # Application entry point
└── requirements.txt         # Python dependencies
```

## Database Schema

- **users**: League participants (username, email, display_name, starting_bankroll)
- **games**: NFL games (game_id, week, home/away teams, kickoff, results)
- **picks**: User selections (user, game, player, odds, result, payout)
- **bankroll_history**: Weekly bankroll snapshots

## Grading Workflow

### Automated Grading
```bash
python auto_grade.py --week 10
```

### Manual Grading
```bash
python grade_week.py --week 10
```

The grading process:
1. Loads game results from NFL play-by-play data
2. Identifies first TD scorers for each game
3. Updates pick results (win/loss/push)
4. Calculates payouts based on American odds
5. Updates user bankrolls

## Key Features

### Pick Submission
- Browse upcoming games for the week
- View player statistics and trends
- See current odds from multiple sportsbooks
- Submit picks before game kickoff

### League Management
- View all user picks for transparency
- Track weekly performance
- Monitor overall standings
- Export data for analysis

### Data Integration
Uses the shared `nfl_core` package for:
- NFL play-by-play data via nflreadpy
- First TD scorer statistics
- Red zone and opening drive analysis
- Defense rankings and funnel identification

## Data Caching

- Play-by-play data cached in `main/cache/` as Parquet files
- Odds cached for 30 minutes to reduce API calls
- Database stored in `instance/league.db`

## Tips for League Admins

- Run grading Monday/Tuesday after all games complete
- Verify results before finalizing (handles stat corrections)
- Set pick deadlines to game kickoff times
- Review bankroll history for accuracy
- Back up the database regularly

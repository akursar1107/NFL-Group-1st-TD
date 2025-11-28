# NFL First TD League Web App

A Flask-based web application for managing an NFL First Touchdown betting league.

## Setup

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables** (create `.env` file):
   ```
   SECRET_KEY=your-secret-key-here
   ODDS_API_KEY=your-odds-api-key-here
   ```

4. **Initialize database**:
   ```bash
   python init_db.py
   ```

5. **Run the application**:
   ```bash
   python run.py
   ```

6. **Access the app**: Open browser to `http://localhost:5000`

## Project Structure

```
league_webapp/
├── app/
│   ├── __init__.py          # App factory
│   ├── config.py            # Configuration
│   ├── models.py            # Database models
│   ├── routes.py            # Web routes
│   ├── templates/           # HTML templates
│   ├── static/              # CSS, JS, images
│   └── nfl_utils/           # NFL data utilities
├── instance/                # SQLite database (auto-created)
├── init_db.py              # Database initialization
├── run.py                  # Application entry point
└── requirements.txt        # Dependencies
```

## Database Schema

- **users**: League participants (username, email, display_name)
- **games**: NFL games (game_id, week, teams, results)
- **picks**: User selections (player, odds, result, payout)
- **bankroll_history**: Running totals by week

## Next Steps

- [ ] Copy NFL utilities from CLI tool (`stats.py`, `odds.py`, `data.py`)
- [ ] Create CSV import script for historical data
- [ ] Add auto-grading functionality
- [ ] Build pick submission forms
- [ ] Add standings calculations

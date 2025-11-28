# NFL First TD Betting Analytics Platform

A comprehensive platform for analyzing NFL First Touchdown scorer data, calculating Expected Value, and managing a betting league. Consists of a CLI tool for odds analysis and a web application for league management.

## 📦 Project Structure

```
main/
├── firstTD_CLI/          # Command-line odds analyzer
├── league_webapp/        # Flask web app for league management
├── nfl_core/             # Shared statistics & data utilities
├── cache/                # NFL data & odds cache
└── venv/                 # Python virtual environment
```

## 🎯 Features

### CLI Tool (firstTD_CLI)
- **Historical Analysis**: Track First TD scorers for every game
- **Live Odds Integration**: Real-time odds from The Odds API
- **EV Scanner**: Find positive Expected Value bets
- **Advanced Analytics**: Red zone stats, opening drive usage, defense rankings
- **Funnel Defense Detection**: Identify pass/run funnel defenses
- **Kelly Criterion**: Optimal bet sizing calculations

### Web Application (league_webapp)
- **League Management**: User accounts and standings
- **Pick Submission**: Weekly pick entry with odds tracking
- **Auto-Grading**: Automatic result verification from play-by-play data
- **Bankroll Tracking**: Running totals and profit/loss
- **Admin Tools**: Quick grading, pick editing, user management
- **Statistics Dashboard**: Season-long performance metrics

### Shared Package (nfl_core)
- **First TD Detection**: Process NFL play-by-play data
- **Player Statistics**: Calculate probabilities and rankings
- **Defense Analysis**: Rank defenses vs positions
- **Data Caching**: Fast parquet-based caching
- **Odds Conversion**: American odds ↔ probability

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- API key from [The Odds API](https://the-odds-api.com/)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd main
   ```

2. **Activate virtual environment**:
   ```bash
   # Windows
   .\venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install shared package**:
   ```bash
   pip install -e nfl_core
   ```

4. **Set API key** (required for CLI tool):
   ```bash
   # Windows PowerShell
   $env:ODDS_API_KEY="your_api_key_here"
   
   # macOS/Linux
   export ODDS_API_KEY="your_api_key_here"
   ```

### Running the CLI Tool

```bash
cd firstTD_CLI
python main.py
```

**Menu Options:**
1. Weekly Schedule & Odds
2. Current Week Odds
3. Team History
4. Player Stats
5. Team Stats Analysis
6. Defense vs Position
7. Opening Drive Stats
8. Home/Away Splits
9. **Best Bets Scanner** ⭐

### Running the Web App

```bash
cd league_webapp
python run.py
```

Access at: `http://localhost:5000`

**First-time setup:**
```bash
# Initialize database
python scripts/setup/init_db.py

# Add admin user
python scripts/setup/add_user.py
```

## 📊 How It Works

### Data Flow
1. **NFL Data**: Uses `nflreadpy` to fetch play-by-play, schedule, and roster data
2. **Caching**: Stores parquet files in `cache/` for fast reloading
3. **First TD Detection**: Analyzes play-by-play to find first TD scorer in each game
4. **Statistics**: Calculates player probabilities, defense rankings, red zone usage
5. **EV Calculation**: Compares probabilities with bookmaker odds to find +EV bets

### Example: Finding +EV Bets

```python
from nfl_core.data import load_data_with_cache
from nfl_core.stats import get_first_td_scorers, get_player_season_stats

# Load data
schedule_df, pbp_df, roster_df = load_data_with_cache(2025)

# Get historical first TD scorers
first_td_map = get_first_td_scorers(pbp_df, roster_df=roster_df)

# Calculate player probabilities (last 5 games)
player_stats = get_player_season_stats(schedule_df, first_td_map, last_n_games=5)

# Player shows 15% probability, but odds are +800 (11.1% implied)
# This is a +EV bet!
```

## 🛠️ Tech Stack

- **Backend**: Flask, SQLAlchemy, Flask-Caching
- **Data Processing**: Polars (10x faster than pandas)
- **NFL Data**: nflreadpy (play-by-play, schedule, rosters)
- **Odds API**: The Odds API (real-time bookmaker odds)
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript (minimal)

## 📖 Documentation

### CLI Tool
See [firstTD_CLI/README.md](firstTD_CLI/README.md) for detailed usage.

### Web Application
See [league_webapp/README.md](league_webapp/README.md) for setup and features.

### Shared Package
See [nfl_core/README.md](nfl_core/README.md) for API documentation.

## 🔧 Configuration

### Environment Variables
```bash
ODDS_API_KEY=your_api_key      # Required for CLI tool
SECRET_KEY=random_secret       # Required for web app
```

### Cache Settings
- **Location**: `cache/` (relative to main/)
- **Schedule/PBP/Roster**: Parquet files per season
- **Odds Cache**: 1 hour expiry (configurable in `nfl_core/config.py`)

## 📁 Key Files

```
main/
├── firstTD_CLI/
│   ├── main.py              # CLI entry point
│   ├── ui.py                # Display formatting
│   ├── odds.py              # Odds API integration
│   └── config.py            # CLI configuration
│
├── league_webapp/
│   ├── run.py               # Web app entry point
│   ├── app/
│   │   ├── routes.py        # Web routes
│   │   ├── models.py        # Database models
│   │   └── templates/       # HTML templates
│   ├── grade_week.py        # Manual grading script
│   └── auto_grade.py        # Automated grading
│
└── nfl_core/
    ├── stats.py             # 10 statistics functions
    ├── data.py              # Data loading with caching
    └── config.py            # Shared configuration
```

## 🎓 Usage Examples

### Find Best Bets for Current Week
```bash
cd firstTD_CLI
python main.py
# Select option 9: Best Bets Scanner
```

### Grade Completed Week
```bash
cd league_webapp
python grade_week.py
# Enter week number to grade
```

### Check League Standings
Navigate to `http://localhost:5000` after starting web app.

## 🤝 Contributing

This is a personal project, but feel free to fork and adapt for your own league!

## 📄 License

This project is for personal use. NFL data provided by nflreadpy/nflverse.

## ⚠️ Disclaimer

This tool is for educational and entertainment purposes only. Gambling involves risk. Please gamble responsibly and within your means.

## 🔮 Future Enhancements

- [ ] Player injury data integration
- [ ] Weather impact analysis
- [ ] Machine learning probability models
- [ ] Discord/Slack bot integration
- [ ] Mobile-responsive web design
- [ ] API endpoints for picks submission
- [ ] Historical bet tracking and ROI analysis

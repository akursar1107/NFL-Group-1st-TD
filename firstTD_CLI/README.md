# NFL First TD Tracker & Odds Analyzer

A command-line tool that analyzes NFL First Touchdown scorer data and compares it with real-time odds to find positive Expected Value (EV) bets.

## Features

- **Historical Analysis**: Tracks First TD scorers for every game in the season
- **Funnel Defense Identification**: Spots defenses that are weak against specific play types (Run vs Pass)
- **EV Scanner**: Calculates Expected Value for bets based on historical hit rates vs bookmaker odds
- **Red Zone & Opening Drive Stats**: Deep dive into player usage in critical situations
- **Kelly Criterion**: Optimal bet sizing based on edge and bankroll

## Prerequisites

- Python 3.10 or higher
- Virtual environment (recommended)
- API key from [The Odds API](https://the-odds-api.com/)

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

4. **Install CLI dependencies**:
   ```bash
   pip install -r firstTD_CLI/requirements.txt
   ```

5. **Set API Key**:
   Create a `.env` file in the main directory or set as environment variable:
   
   **Windows (PowerShell)**:
   ```powershell
   $env:ODDS_API_KEY="your_api_key_here"
   ```
   
   **Mac/Linux**:
   ```bash
   export ODDS_API_KEY="your_api_key_here"
   ```

## Usage

1. **Navigate to CLI directory**:
   ```bash
   cd firstTD_CLI
   ```

2. **Run the tool**:
   ```bash
   python main.py
   ```

3. **Follow the menu**:
   - View NFL schedule for current week
   - Check odds for specific games
   - Run the "Best Bets Scanner" to find +EV opportunities
   - View detailed player statistics

## How It Works

The tool uses the shared `nfl_core` package to:
1. Load NFL play-by-play data from nflreadpy
2. Calculate first TD scorer rates by player and situation
3. Fetch real-time odds from multiple sportsbooks
4. Identify bets where your calculated probability exceeds the implied odds
5. Apply Kelly Criterion for optimal bet sizing

## Data Caching

Play-by-play data is cached in `main/cache/` as Parquet files for fast access. Odds are cached for 30 minutes to avoid excessive API calls.

## Tips

- Focus on games with identified "funnel" defenses
- Check red zone usage and opening drive tendencies
- Compare hit rates across multiple weeks
- Use Kelly Criterion for bankroll management

# NFL First TD League Web App

A full-stack web application for managing an NFL First Touchdown (FTD) and Anytime Touchdown Scorer (ATTS) betting league with bankroll tracking, pick management, and automated grading.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 16+ (for React frontend)
- API key from [The Odds API](https://the-odds-api.com/) (optional)

### Backend Setup (Flask)
```bash
cd main
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
pip install -r league_webapp/requirements.txt

cd league_webapp
flask db upgrade      # Run database migrations
python run.py         # Start server on http://localhost:5000
```

### Frontend Setup (React)
```bash
cd frontend
npm install
npm start  # Start dev server on http://localhost:3000
```

## 📚 Documentation

Comprehensive documentation is available in the `docs/` folder:

- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design, data flow, and component structure
- **[API Reference](docs/API.md)** - Complete endpoint documentation with examples
- **[Development Guide](docs/DEVELOPMENT.md)** - Local setup, workflows, and testing
- **[Database Guide](docs/DATABASE.md)** - Schema, migrations, and data management
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment instructions
- **[Refactoring Log](docs/REFACTORING.md)** - Phase 1 & 2 improvements history

## ✨ Features

### For Users
- 📊 **Live Standings** - Real-time leaderboard with bankroll tracking
- 🎯 **Pick Submission** - Submit FTD and ATTS picks with odds
- 📈 **Analytics** - Player stats, defense rankings, and trends
- 💰 **Best Bets** - AI-powered positive EV opportunities
- 📅 **Weekly View** - See all games and picks for any week

### For Admins
- ⚡ **Auto-Grading** - Automated pick grading from NFL play-by-play data
- 🔧 **Admin Dashboard** - User management and system stats
- 📥 **Data Import** - Bulk import NFL schedule and results
- 🎲 **Odds Integration** - Real-time odds from multiple sportsbooks

## 🛠️ Tech Stack

### Backend
- **Flask** - Web framework with Blueprint architecture
- **SQLAlchemy** - ORM with migration support (Flask-Migrate)
- **SQLite** - Database (PostgreSQL-ready for production)
- **Flask-Caching** - Response caching for performance
- **Marshmallow** - Input validation and serialization

### Frontend
- **React** - Modern UI with TypeScript
- **React Router** - Client-side routing
- **CSS Modules** - Scoped component styling

### Data & Analytics
- **nfl_core** - Custom package for NFL stats (nflreadpy)
- **Polars** - Fast DataFrame processing
- **The Odds API** - Live sportsbook odds

### Data & Analytics
- **nfl_core** - Custom package for NFL stats (nflreadpy)
- **Polars** - Fast DataFrame processing
- **The Odds API** - Live sportsbook odds

## 📊 Project Structure

```
main/
├── league_webapp/          # Flask backend
│   ├── app/
│   │   ├── blueprints/    # API routes (modular structure)
│   │   ├── services/      # Business logic layer
│   │   ├── models.py      # Database models
│   │   ├── config.py      # Environment configs
│   │   └── middleware.py  # Performance monitoring
│   ├── instance/          # SQLite database
│   ├── migrations/        # Database migrations
│   └── run.py            # Flask entry point

frontend/
├── src/
│   ├── api/              # TypeScript API clients
│   ├── pages/            # React components
│   └── styles/           # CSS modules
└── package.json

docs/                      # Detailed documentation
```

## 🧪 Testing

```bash
# Run backend tests
cd main/league_webapp
pytest

# Run with coverage
pytest --cov=app tests/

# Run frontend tests
cd frontend
npm test
```

## 📈 Performance

- **Caching**: 60-80% reduction in database queries
- **Response Times**: 
  - Cached endpoints: <10ms
  - Uncached endpoints: 20-100ms
- **Monitoring**: Request timing and slow query detection
- **Optimization**: Eager loading prevents N+1 queries

## 🔒 Security

- CORS configured for React frontend (localhost:3000)
- Input validation via Marshmallow schemas
- SQL injection protection via SQLAlchemy ORM
- CSRF protection enabled (Flask-WTF)

## 🤝 Contributing

1. Create a feature branch from `develop`
2. Make your changes with tests
3. Run `pytest` and ensure all tests pass
4. Submit a pull request to `develop`

## 📝 License

Private project for personal use.

## 🙏 Acknowledgments

- NFL play-by-play data via [nflreadpy](https://github.com/greerreNFL/nflreadpy)
- Odds data from [The Odds API](https://the-odds-api.com/)

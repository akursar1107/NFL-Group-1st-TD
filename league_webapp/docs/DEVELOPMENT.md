# Development Guide

Complete guide for setting up and working with the application in development.

## Initial Setup

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd nfl-ftd-league
```

### 2. Backend Setup (Flask)

```bash
# Navigate to main directory
cd main

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Windows CMD:
venv\Scripts\activate.bat

# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r league_webapp/requirements.txt

# Navigate to webapp
cd league_webapp

# Run database migrations
flask db upgrade

# Start Flask server
python run.py
```

Flask server will run on **http://localhost:5000**

### 3. Frontend Setup (React)

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start React dev server
npm start
```

React app will run on **http://localhost:3000**

## Environment Variables

Create a `.env` file in `main/league_webapp/`:

```env
# Required
SECRET_KEY=your-random-secret-key-here

# Optional (for odds data)
ODDS_API_KEY=your-odds-api-key

# Environment (development, production, testing)
FLASK_ENV=development
```

### Generating SECRET_KEY

```python
import secrets
print(secrets.token_hex(32))
```

## Database Management

### Creating Migrations

After modifying models in `app/models.py`:

```bash
cd main/league_webapp

# Auto-generate migration
flask db migrate -m "Description of changes"

# Review the generated migration file in migrations/versions/

# Apply migration
flask db upgrade

# Rollback last migration (if needed)
flask db downgrade
```

### Manual Database Operations

```bash
# Open SQLite shell
sqlite3 instance/league.db

# View tables
.tables

# View schema
.schema users

# Query data
SELECT * FROM users;

# Exit
.quit
```

### Reset Database

```bash
# Delete database
rm instance/league.db

# Recreate with migrations
flask db upgrade
```

## Development Workflow

### Starting Development Session

```bash
# Terminal 1: Flask Backend
cd main/league_webapp
..\venv\Scripts\Activate.ps1  # Windows
python run.py

# Terminal 2: React Frontend
cd frontend
npm start
```

### Making Changes

**Backend (Python):**
1. Edit files in `main/league_webapp/app/`
2. Flask auto-reloads on file changes (debug mode)
3. Test endpoint with browser or curl
4. Write tests in `tests/`

**Frontend (TypeScript/React):**
1. Edit files in `frontend/src/`
2. React hot-reloads automatically
3. Check browser console for errors
4. Write tests with Jest/React Testing Library

### Code Style

**Python (Backend):**
- Follow PEP 8
- Use type hints where helpful
- Docstrings for functions/classes
- Max line length: 100 characters

**TypeScript (Frontend):**
- Use TypeScript strict mode
- Prefer functional components with hooks
- Use async/await over promises
- CSS Modules for styling

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name develop

# Make changes and commit
git add .
git commit -m "Add feature description"

# Push to GitHub
git push origin feature/your-feature-name

# Create Pull Request to develop branch
```

## Testing

### Backend Tests

```bash
cd main/league_webapp

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::test_get_standings

# Run with verbose output
pytest -v
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- Standings.test.tsx
```

### Manual Testing Checklist

After making changes:

- [ ] Flask server starts without errors
- [ ] React app compiles successfully
- [ ] No errors in browser console
- [ ] API endpoints return correct data
- [ ] Database migrations apply cleanly
- [ ] All automated tests pass

## Debugging

### Flask Debugging

**Enable SQL Query Logging:**

In `app/config.py`:
```python
class DevelopmentConfig(Config):
    SQLALCHEMY_ECHO = True  # Log all SQL queries
```

**Access Flask Shell:**

```bash
cd main/league_webapp
flask shell

# Now you can interact with models
>>> from app.models import User, Pick
>>> User.query.all()
>>> Pick.query.filter_by(user_id=1).count()
```

**View Performance Logs:**

Check console output for:
- Slow requests (>1s)
- Slow queries (>100ms)
- High query counts (>10 per request)

### React Debugging

**React DevTools:**
- Install [React DevTools](https://react-devtools.netlify.app/)
- Inspect component state and props
- Profile component renders

**Network Tab:**
- Check API requests in browser DevTools
- Verify request/response data
- Check response times

**Console Logging:**
```typescript
console.log('State:', standings);
console.table(standings); // Nice table format
```

## Common Tasks

### Adding a New API Endpoint

1. **Create route in blueprint:**

```python
# app/blueprints/api/my_feature.py
from flask import Blueprint, jsonify
from .. import cache

my_bp = Blueprint('my_feature', __name__)

@my_bp.route('/my-endpoint', methods=['GET'])
@cache.cached(timeout=60)
def get_my_data():
    # Your logic here
    return jsonify({'data': 'value'}), 200
```

2. **Register blueprint:**

```python
# app/blueprints/api/__init__.py
from .my_feature import my_bp

def register_blueprints(app):
    # ... existing blueprints
    app.register_blueprint(my_bp, url_prefix='/api')
```

3. **Create TypeScript client:**

```typescript
// frontend/src/api/myFeature.ts
export async function fetchMyData() {
  const response = await fetch('http://localhost:5000/api/my-endpoint');
  if (!response.ok) throw new Error('Failed to fetch');
  return response.json();
}
```

4. **Use in React component:**

```typescript
// frontend/src/pages/MyPage.tsx
import { fetchMyData } from '../api/myFeature';

export function MyPage() {
  useEffect(() => {
    fetchMyData().then(data => console.log(data));
  }, []);
}
```

### Adding a Database Column

1. **Update model:**

```python
# app/models.py
class User(db.Model):
    # ... existing columns
    new_column = db.Column(db.String(100), nullable=True)
```

2. **Create migration:**

```bash
flask db migrate -m "Add new_column to users"
```

3. **Review migration file**, then apply:

```bash
flask db upgrade
```

### Clearing Cache

```bash
# Restart Flask server (clears SimpleCache)
# Or programmatically:
flask shell
>>> from app import cache
>>> cache.clear()
```

## Performance Optimization

### Monitor Slow Endpoints

Check console for logs like:
```
Slow request: GET /api/standings took 1.234s | Status: 200
```

### Monitor Database Queries

```
Slow query (0.150s): SELECT * FROM picks WHERE ...
High query count: GET /api/week-detail executed 15 queries
```

### Add Caching

```python
@api_bp.route('/expensive-endpoint')
@cache.cached(timeout=300, query_string=True)
def expensive_operation():
    # Heavy computation here
    return jsonify(result)
```

### Optimize Queries

Use eager loading to prevent N+1:

```python
# Bad (N+1 queries)
picks = Pick.query.all()
for pick in picks:
    user = pick.user  # Additional query per pick

# Good (1 query)
from sqlalchemy.orm import joinedload
picks = Pick.query.options(joinedload(Pick.user)).all()
```

## Troubleshooting

### "Module not found" errors

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Database locked errors

```bash
# Close all connections, restart Flask server
# Or delete database and recreate:
rm instance/league.db
flask db upgrade
```

### CORS errors in browser

Check `app/__init__.py` has:
```python
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
```

### Port already in use

```bash
# Kill process on port 5000
netstat -ano | findstr :5000
taskkill /PID <pid> /F

# Or change Flask port in run.py:
app.run(port=5001)
```

## Useful Commands

```bash
# Backend
flask --version                 # Check Flask version
flask routes                    # List all routes
flask db current                # Show current migration
flask db history                # Show migration history
pip freeze > requirements.txt   # Update dependencies

# Frontend
npm list                        # Show installed packages
npm outdated                    # Check for updates
npm run build                   # Production build
npm run lint                    # Run ESLint
```

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Flask-Migrate Guide](https://flask-migrate.readthedocs.io/)

# Quick Start Guide

## First Time Setup

1. **Check you're in the right directory:**
   ```powershell
   cd "C:\Users\akurs\Desktop\Vibe Coder\main"
   ```

2. **Activate virtual environment:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies (if needed):**
   ```powershell
   pip install -r requirements-dev.txt
   ```

4. **Start Flask backend:**
   ```powershell
   python league_webapp\run.py
   ```
   - Flask runs at: `http://localhost:5000`

5. **Start React frontend (new terminal):**
   ```powershell
   cd frontend
   npm start
   ```
   - React runs at: `http://localhost:3000`

## Daily Development

### Which app should I use?
- **React app** (`localhost:3000`): Modern UI, faster, better UX
- **Flask templates** (`localhost:5000`): Legacy, will be deprecated

### Common Tasks

**View Analysis page:**
- React: `http://localhost:3000/analysis`
- Flask: `http://localhost:5000/analysis`

**Make changes to Analysis page:**
- React: Edit `frontend/src/pages/Analysis.tsx` + `league_webapp/app/blueprints/api/analysis.py`
- Flask: Edit `league_webapp/app/templates/analysis.html` + `league_webapp/app/routes.py`

**After making Python changes:**
1. Flask auto-reloads (usually)
2. If it doesn't work:
   ```powershell
   # Kill Flask
   Stop-Process -Name python -Force
   
   # Clear cache
   Get-ChildItem -Path ".\league_webapp" -Filter "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force
   
   # Restart Flask
   python league_webapp\run.py
   ```

**After making React changes:**
1. React hot-reloads automatically
2. If it doesn't work: Hard refresh (`Ctrl + Shift + R`)

## Troubleshooting

**Changes not showing?** → See `DEVELOPMENT_GUIDE.md`

**Percentages showing 9170% instead of 91.7%?**
- You're viewing React but edited Flask (or vice versa)
- Check your browser URL: `localhost:5000` or `localhost:3000`?

**Multiple Flask processes running?**
```powershell
# Check what's running
Get-Process -Name python

# Kill all Python processes
Stop-Process -Name python -Force
```

**Port already in use?**
```powershell
# Find what's using port 5000
netstat -ano | findstr :5000

# Kill that process ID
Stop-Process -Id <PID> -Force
```

## Git Workflow

```powershell
# Check status
git status

# See changes
git diff

# Stage all changes
git add -A

# Commit
git commit -m "Description of changes"

# Push to develop branch
git push origin develop
```

## Project Structure

```
main/
├── league_webapp/          # Flask backend
│   ├── app/
│   │   ├── blueprints/
│   │   │   ├── api/        # API endpoints for React
│   │   │   └── ...
│   │   ├── templates/      # HTML templates (legacy)
│   │   └── routes.py       # Flask routes
│   └── run.py              # Flask entry point
│
├── frontend/               # React frontend
│   ├── src/
│   │   ├── pages/          # React pages
│   │   ├── api/            # API client functions
│   │   └── ...
│   └── package.json
│
├── nfl_core/               # Shared Python logic
├── cache/                  # Cached NFL data
└── instance/               # SQLite database
```

## Next Steps

1. Read `DEVELOPMENT_GUIDE.md` for common issues
2. Read `Frontend Conversion TODO.md` for migration plan
3. Commit your work frequently
4. Use React app (port 3000) for daily use

# Deployment Guide

Guide for deploying the NFL First TD League application to production.

## Overview

The application consists of two parts:
1. **Backend (Flask API)** - Deployed to a Python hosting service
2. **Frontend (React SPA)** - Deployed to a static hosting service

## Recommended Stack

### Option 1: Free Tier (Hobby)
- **Backend:** Railway, Render, or Heroku (free tier)
- **Frontend:** Vercel, Netlify, or CloudFlare Pages
- **Database:** Heroku Postgres (hobby tier) or Railway

### Option 2: Scalable (Production)
- **Backend:** AWS Elastic Beanstalk, Google Cloud Run, or DigitalOcean
- **Frontend:** CloudFlare CDN or AWS CloudFront + S3
- **Database:** AWS RDS PostgreSQL or managed PostgreSQL

## Pre-Deployment Checklist

- [ ] Set strong `SECRET_KEY` in environment variables
- [ ] Configure production database (PostgreSQL)
- [ ] Update CORS to allow production frontend URL
- [ ] Set `FLASK_ENV=production`
- [ ] Test all API endpoints
- [ ] Run database migrations
- [ ] Create production `.env` file
- [ ] Set up error monitoring (Sentry)
- [ ] Configure logging
- [ ] Test with production data

## Backend Deployment (Flask)

### 1. Prepare Application

**Update `app/config.py`:**

```python
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # HTTPS only
    
    # Use environment variable for database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
```

**Update CORS in `app/__init__.py`:**

```python
# Allow production frontend
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://your-app.vercel.app",
            "http://localhost:3000"  # Keep for local dev
        ]
    }
})
```

**Create `Procfile` (for Heroku/Railway):**

```
web: cd main/league_webapp && gunicorn run:app
```

**Create `runtime.txt`:**

```
python-3.10.11
```

**Update `requirements.txt`:**

```bash
cd main/league_webapp
pip freeze > requirements.txt
```

Add production server:
```
gunicorn==21.2.0
psycopg2-binary==2.9.9  # For PostgreSQL
```

### 2. Deploy to Railway (Recommended)

**Via Railway CLI:**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
cd main/league_webapp
railway init

# Add PostgreSQL database
railway add --database postgresql

# Set environment variables
railway variables set FLASK_ENV=production
railway variables set SECRET_KEY=<your-secret-key>

# Deploy
railway up
```

**Or via GitHub Integration:**

1. Push code to GitHub
2. Go to [Railway](https://railway.app)
3. Create new project from GitHub repo
4. Add PostgreSQL database
5. Set environment variables in Railway dashboard
6. Deploy automatically on push

**Run Migrations:**

```bash
# Via Railway CLI
railway run flask db upgrade
```

### 3. Deploy to Heroku

```bash
# Install Heroku CLI
brew install heroku/brew/heroku  # Mac
# or download from heroku.com

# Login
heroku login

# Create app
cd main/league_webapp
heroku create your-app-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=<your-secret-key>
heroku config:set ODDS_API_KEY=<your-api-key>

# Deploy
git push heroku main

# Run migrations
heroku run flask db upgrade

# Open app
heroku open
```

### 4. Deploy to Render

1. Go to [Render](https://render.com)
2. Create new **Web Service** from GitHub repo
3. Configure:
   - **Root Directory:** `main/league_webapp`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn run:app`
4. Add PostgreSQL database
5. Set environment variables
6. Deploy

## Frontend Deployment (React)

### 1. Prepare Application

**Update API base URL in `frontend/src/api/`:**

Create `frontend/src/config.ts`:

```typescript
export const API_BASE_URL = 
  process.env.NODE_ENV === 'production'
    ? 'https://your-api.railway.app/api'
    : 'http://localhost:5000/api';
```

**Update API clients to use config:**

```typescript
// frontend/src/api/standings.ts
import { API_BASE_URL } from '../config';

export async function fetchStandings(season: number) {
  const response = await fetch(`${API_BASE_URL}/standings?season=${season}`);
  // ...
}
```

**Build for production:**

```bash
cd frontend
npm run build
```

This creates an optimized build in `frontend/build/`.

### 2. Deploy to Vercel (Recommended)

**Via Vercel CLI:**

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
cd frontend
vercel

# Or deploy to production
vercel --prod
```

**Via GitHub Integration:**

1. Push code to GitHub
2. Go to [Vercel](https://vercel.com)
3. Import GitHub repository
4. Configure:
   - **Framework:** Create React App
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `build`
5. Add environment variable:
   - `REACT_APP_API_URL=https://your-api.railway.app/api`
6. Deploy

### 3. Deploy to Netlify

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Deploy
cd frontend
netlify deploy --prod --dir=build
```

**Or via GitHub Integration:**

1. Go to [Netlify](https://netlify.com)
2. Import GitHub repository
3. Configure:
   - **Base directory:** `frontend`
   - **Build command:** `npm run build`
   - **Publish directory:** `frontend/build`
4. Add environment variables
5. Deploy

### 4. Deploy to CloudFlare Pages

1. Go to [CloudFlare Pages](https://pages.cloudflare.com)
2. Connect GitHub repository
3. Configure:
   - **Build command:** `cd frontend && npm install && npm run build`
   - **Build output:** `frontend/build`
4. Deploy

## Database Setup

### PostgreSQL Migration

**1. Create PostgreSQL Database:**

- Heroku: `heroku addons:create heroku-postgresql`
- Railway: Add PostgreSQL via dashboard
- AWS RDS: Create PostgreSQL instance

**2. Get Database URL:**

```bash
# Heroku
heroku config:get DATABASE_URL

# Railway
railway variables get DATABASE_URL
```

**3. Update Environment Variable:**

```bash
# Format: postgresql://user:password@host:port/database
export DATABASE_URL=postgresql://user:pass@host:5432/db
```

**4. Run Migrations:**

```bash
# On production server
flask db upgrade

# Or via Railway
railway run flask db upgrade

# Or via Heroku
heroku run flask db upgrade
```

**5. Import Data (if needed):**

```python
# Create admin script to import data
# Or use SQL dump
pg_dump local_db > dump.sql
psql $DATABASE_URL < dump.sql
```

## Environment Variables

### Backend (Flask)

Required:
```env
FLASK_ENV=production
SECRET_KEY=<64-char-random-string>
DATABASE_URL=postgresql://user:pass@host:port/database
```

Optional:
```env
ODDS_API_KEY=<your-odds-api-key>
SENTRY_DSN=<your-sentry-dsn>
```

### Frontend (React)

```env
REACT_APP_API_URL=https://your-api.railway.app/api
```

## Monitoring & Logging

### Error Tracking (Sentry)

**1. Install Sentry:**

```bash
pip install sentry-sdk[flask]
```

**2. Configure in `app/__init__.py`:**

```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Initialize Sentry
    if app.config.get('SENTRY_DSN'):
        sentry_sdk.init(
            dsn=app.config['SENTRY_DSN'],
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0
        )
    
    # ... rest of setup
```

**3. Set environment variable:**

```bash
export SENTRY_DSN=https://your-key@sentry.io/project-id
```

### Logging

**Configure production logging:**

```python
# app/config.py
class ProductionConfig(Config):
    LOG_LEVEL = 'WARNING'
    
# app/middleware.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    if not app.debug:
        file_handler = RotatingFileHandler(
            'logs/app.log',
            maxBytes=10240000,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)
```

## Security

### HTTPS

- Ensure all production URLs use HTTPS
- Set `SESSION_COOKIE_SECURE = True` in production config
- Use secure connection strings for database

### Secrets Management

Never commit:
- `.env` files
- `SECRET_KEY`
- Database credentials
- API keys

Use platform secret management:
- Heroku: Config Vars
- Railway: Environment Variables
- AWS: Secrets Manager
- Render: Secret Files

### Rate Limiting

Install Flask-Limiter:

```bash
pip install flask-limiter
```

Configure:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# On specific routes
@api_bp.route('/picks', methods=['POST'])
@limiter.limit("10 per minute")
def create_pick():
    # ...
```

## Performance

### CDN for Frontend

Use CloudFlare or AWS CloudFront to cache static assets.

### Database Connection Pooling

Already configured in production config:

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}
```

### Caching

Consider Redis for production caching:

```python
# Update cache config
CACHE_TYPE = 'RedisCache'
CACHE_REDIS_URL = os.environ.get('REDIS_URL')
```

## Backup Strategy

### Database Backups

**Heroku:**
```bash
# Capture backup
heroku pg:backups:capture

# Download backup
heroku pg:backups:download
```

**Railway/Render:**
- Use platform backup features
- Or run pg_dump on schedule

**Manual:**
```bash
# Backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore
psql $DATABASE_URL < backup_20251130.sql
```

### Automated Backups

Create cron job or scheduled task:

```bash
# crontab -e
0 2 * * * pg_dump $DATABASE_URL > /backups/backup_$(date +\%Y\%m\%d).sql
```

## Rollback Strategy

### Code Rollback

```bash
# Heroku
heroku rollback

# Railway/Vercel/Netlify
# Use dashboard to rollback to previous deployment
```

### Database Rollback

```bash
# Downgrade one migration
flask db downgrade

# Or restore from backup
psql $DATABASE_URL < backup.sql
```

## Health Checks

Create health endpoint:

```python
# app/blueprints/api/__init__.py
@api_bp.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200
```

Configure platform health checks to hit `/api/health`.

## Troubleshooting

### Build Failures

- Check Python version matches `runtime.txt`
- Verify all dependencies in `requirements.txt`
- Check build logs for errors

### Database Connection Errors

- Verify `DATABASE_URL` format
- Check database is running
- Verify network access/firewall rules

### CORS Errors

- Update CORS to include production frontend URL
- Check frontend is sending correct Origin header

### 500 Errors

- Check application logs
- Verify all environment variables set
- Test locally with production config

## Monitoring Dashboards

Recommended tools:
- **Sentry** - Error tracking
- **Datadog** - Performance monitoring
- **LogRocket** - Frontend session replay
- **Heroku Metrics** - Built-in metrics
- **Railway Metrics** - Built-in metrics

## Cost Optimization

### Free Tier Options

- Heroku: 1000 free dyno hours/month
- Railway: $5 free credit/month
- Vercel: Unlimited hobby projects
- Netlify: 100GB bandwidth/month

### Paid Tier

Estimate for small league (~20 users):
- Railway Hobby: $5-10/month
- Heroku Eco: $5/month
- PostgreSQL: $7-15/month
- Frontend: Free (Vercel/Netlify)

**Total: ~$12-25/month**

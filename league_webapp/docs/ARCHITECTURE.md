# Architecture Guide

## System Overview

The NFL First TD League application uses a modern **full-stack architecture** with a clear separation between frontend and backend layers.

```
┌─────────────────────────────────────────────────────────┐
│                  FRONTEND LAYER                          │
├──────────────────────────────────────────────────────────┤
│  React App (TypeScript)                                  │
│  Port: 3000                                              │
│  - Client-side routing                                   │
│  - Dynamic UI updates                                    │
│  - API calls via fetch()                                 │
└─────────────────────────────────────────────────────────┘
                         ↓ HTTP/JSON
┌─────────────────────────────────────────────────────────┐
│                  BACKEND LAYER (Flask)                   │
├─────────────────────────────────────────────────────────┤
│  Port: 5000                                              │
│  ┌──────────────────────────────────────────────────┐   │
│  │  API Blueprints (/api/*)                         │   │
│  │  - standings    - Leaderboard data               │   │
│  │  - picks        - CRUD for picks                 │   │
│  │  - games        - Games, users, week details     │   │
│  │  - analysis     - Best bets, player stats        │   │
│  │  - admin        - Dashboard, grading             │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Services Layer (Business Logic)                 │   │
│  │  - StatsService     - Calculate standings        │   │
│  │  - GradingService   - Auto-grade picks           │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Middleware                                       │   │
│  │  - CORS             - Allow React calls          │   │
│  │  - Performance      - Track response times       │   │
│  │  - Caching          - Speed up queries           │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                         ↓ SQLAlchemy ORM
┌─────────────────────────────────────────────────────────┐
│                  DATABASE LAYER                          │
├─────────────────────────────────────────────────────────┤
│  SQLite: league.db                                      │
│  - users          - League members                      │
│  - games          - NFL schedule                        │
│  - picks          - FTD/ATTS picks                      │
│  - bankroll_history - Historical tracking               │
└─────────────────────────────────────────────────────────┘
```

## Request Flow

### Example: Fetching Standings

```
1. User navigates to /standings in React app
   └─ Component mounts, triggers useEffect()

2. TypeScript API client makes request
   └─ fetchStandings(2025)
   └─ fetch('http://localhost:5000/api/standings?season=2025')

3. Flask receives request
   └─ CORS middleware validates origin
   └─ Performance middleware starts timer
   └─ Route: GET /api/standings

4. Cache layer checks
   └─ If cached (TTL 60s): return immediately
   └─ If not cached: proceed to database

5. Service layer processes
   └─ StatsService.calculate_standings(2025)
   └─ Query database for users and picks
   └─ Calculate wins, losses, bankrolls

6. Response sent
   └─ JSON: { standings: [...], season: 2025 }
   └─ Cache result for 60 seconds
   └─ Add X-Response-Time header

7. React updates UI
   └─ Parse JSON, update state
   └─ Re-render table with standings
```

## Component Architecture

### Backend (Flask)

**Blueprints** - Route organization
```
app/blueprints/
├── api/
│   ├── __init__.py         # Blueprint registration
│   ├── standings.py        # GET /api/standings
│   ├── picks.py            # CRUD /api/picks
│   ├── games.py            # Games and week details
│   ├── analysis.py         # Stats and best bets
│   └── admin.py            # Admin endpoints
├── main.py                 # Legacy Flask templates
└── admin.py                # Legacy admin routes
```

**Services** - Business logic
```
app/services/
├── __init__.py
├── stats_service.py        # Standings calculations
└── grading_service.py      # Pick grading logic
```

**Models** - Database ORM
```
app/models.py
├── User                    # League members
├── Game                    # NFL games
├── Pick                    # User picks (FTD/ATTS)
└── BankrollHistory         # Historical snapshots
```

### Frontend (React)

**Pages** - Route components
```
src/pages/
├── Standings.tsx           # Main leaderboard
├── WeekDetail.tsx          # Week games + picks
├── UserDetail.tsx          # User pick history
├── BestBets.tsx            # Positive EV bets
├── Analysis.tsx            # Player/defense stats
├── AllPicks.tsx            # Admin: all picks view
├── NewPick.tsx             # Admin: create pick
└── EditPick.tsx            # Admin: edit pick
```

**API Layer** - TypeScript clients
```
src/api/
├── standings.ts            # fetchStandings()
├── picks.ts                # createPick(), updatePick()
├── games.ts                # fetchWeekGames()
├── bestBets.ts             # fetchBestBets()
└── admin.ts                # gradeWeek(), importData()
```

## Data Flow Patterns

### Read Operations (GET)
```
React Component
  → API Client (TypeScript)
    → Flask Route
      → Cache Check
        → Service Layer
          → SQLAlchemy Query
            → SQLite Database
          ← Results
        ← Processed Data
      ← Cache + Response
    ← JSON
  ← Update State
← Re-render UI
```

### Write Operations (POST/PUT/DELETE)
```
React Component
  → API Client (TypeScript)
    → Flask Route
      → Input Validation (Marshmallow)
        → Service Layer
          → SQLAlchemy Write
            → SQLite Database
          ← Success
        ← Result
      ← Clear Cache
    ← JSON Response
  ← Update State
← Re-render UI
```

## Caching Strategy

**Cache Timeouts** (configured per endpoint):
- Standings: 60 seconds (frequent updates)
- Best Bets: 1800 seconds (odds API limits)
- Analysis: 300 seconds (heavy computation)
- Week Detail: 60 seconds (active during games)
- User Data: 300 seconds (rarely changes)

**Cache Invalidation**:
- Automatic on POST/PUT/DELETE operations
- Manual via `cache.clear()` in admin actions

## Security Layers

1. **CORS**: Only allows `http://localhost:3000` (React dev)
2. **Input Validation**: Marshmallow schemas validate all inputs
3. **SQL Injection**: SQLAlchemy ORM prevents raw SQL
4. **CSRF Protection**: Flask-WTF tokens (legacy routes)
5. **Session Security**: HTTPOnly, SameSite cookies

## Performance Optimizations

### Database
- **Eager Loading**: `joinedload()` prevents N+1 queries
- **Indexes**: Foreign keys indexed automatically
- **Connection Pooling**: 10 connections max

### Application
- **Caching**: Flask-Caching reduces DB hits by 60-80%
- **Request Monitoring**: Logs slow requests (>1s)
- **Query Monitoring**: Logs slow queries (>100ms)

### Frontend
- **Code Splitting**: Lazy loading with React Router
- **Memoization**: useMemo/useCallback for expensive operations

## Scalability Considerations

**Current (Development)**:
- Single process Flask dev server
- SQLite file database
- SimpleCache (in-memory)

**Production Ready**:
- Gunicorn/uWSGI multi-worker
- PostgreSQL database
- Redis cache backend
- Static frontend (Vercel/CloudFlare)

## Error Handling

**Backend**:
- Try/except blocks in all routes
- Comprehensive error logging
- Consistent JSON error responses
- HTTP status codes (400, 404, 500)

**Frontend**:
- Error boundaries for component crashes
- API error handling with user feedback
- Loading states for async operations

## Monitoring

**Performance Middleware** tracks:
- Request duration (via `X-Response-Time` header)
- Database query count per request
- Slow queries (>100ms)
- Slow requests (>1s)

**Logging Levels**:
- Development: DEBUG (all queries visible)
- Production: WARNING (errors only)

## Future Enhancements

- **Authentication**: JWT tokens, user login
- **WebSockets**: Live game updates
- **API Versioning**: /api/v2/* endpoints
- **Microservices**: Separate grading service
- **CDN**: Static asset delivery
- **Docker**: Containerization for deployment

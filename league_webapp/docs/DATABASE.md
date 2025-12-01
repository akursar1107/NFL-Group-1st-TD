# Database Guide

Complete guide to the database schema, migrations, and data management.

## Schema Overview

The application uses **SQLite** in development and is **PostgreSQL-ready** for production.

### Entity Relationship Diagram

```
┌─────────────┐
│    User     │
│─────────────│
│ id (PK)     │
│ username    │◄─────┐
│ email       │      │
│ is_active   │      │
└─────────────┘      │
                     │
                     │ user_id (FK)
                     │
┌─────────────┐      │      ┌─────────────┐
│    Game     │      │      │    Pick     │
│─────────────│      │      │─────────────│
│ id (PK)     │◄─────┼──────┤ id (PK)     │
│ game_id     │      │      │ user_id     │
│ season      │      └──────┤ game_id     │
│ week        │             │ pick_type   │
│ home_team   │             │ player_name │
│ away_team   │             │ odds        │
│ game_date   │             │ stake       │
│ is_final    │             │ result      │
│ actual_ftd  │             │ payout      │
└─────────────┘             └─────────────┘
```

## Tables

### users

League members who make picks.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | Unique identifier |
| username | VARCHAR(50) | UNIQUE, NOT NULL | Login username |
| email | VARCHAR(100) | UNIQUE, NULLABLE | Email address |
| display_name | VARCHAR(100) | NULLABLE | Display name for UI |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| created_at | DATETIME | DEFAULT NOW | Account creation |

**Example:**
```sql
INSERT INTO users (username, display_name, is_active)
VALUES ('Jeremy', 'Jeremy', 1);
```

### games

NFL game schedule and results.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | Unique identifier |
| game_id | VARCHAR(50) | UNIQUE, NOT NULL | NFL game ID (e.g., "2025_13_DAL_WSH") |
| season | INTEGER | NOT NULL | Season year |
| week | INTEGER | NOT NULL | Week number (1-18) |
| home_team | VARCHAR(10) | NOT NULL | Home team abbreviation |
| away_team | VARCHAR(10) | NOT NULL | Away team abbreviation |
| game_date | DATE | NULLABLE | Date of game |
| game_time | TIME | NULLABLE | Kickoff time |
| is_final | BOOLEAN | DEFAULT FALSE | Game completed |
| actual_first_td_player | VARCHAR(100) | NULLABLE | First TD scorer name |
| created_at | DATETIME | DEFAULT NOW | Record creation |

**Indexes:**
- `idx_game_id` on `game_id`
- `idx_season_week` on `(season, week)`

**Example:**
```sql
INSERT INTO games (game_id, season, week, home_team, away_team, game_date, game_time)
VALUES ('2025_13_DAL_WSH', 2025, 13, 'WSH', 'DAL', '2025-11-28', '16:30:00');
```

### picks

User picks for FTD (First TD) or ATTS (Anytime TD Scorer).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | Unique identifier |
| user_id | INTEGER | FK → users.id | User who made pick |
| game_id | INTEGER | FK → games.id | Game pick is for |
| pick_type | VARCHAR(10) | NOT NULL | "FTD" or "ATTS" |
| player_name | VARCHAR(100) | NOT NULL | Player name |
| player_position | VARCHAR(10) | NULLABLE | Position (RB, WR, TE, QB) |
| odds | INTEGER | NOT NULL | American odds (e.g., +500) |
| stake | DECIMAL(10,2) | DEFAULT 1.0 | Bet amount |
| result | VARCHAR(10) | NULLABLE | "W", "L", "P", or NULL |
| payout | DECIMAL(10,2) | DEFAULT 0.0 | Winnings (stake × odds if W) |
| graded_at | DATETIME | NULLABLE | When pick was graded |
| created_at | DATETIME | DEFAULT NOW | When pick was made |

**Indexes:**
- `idx_user_id` on `user_id`
- `idx_game_id` on `game_id`
- `idx_pick_type` on `pick_type`
- `idx_result` on `result`
- `idx_user_type_result` on `(user_id, pick_type, result)`

**Constraints:**
- UNIQUE on `(user_id, game_id, pick_type)` - One FTD and one ATTS per user per game

**Example:**
```sql
INSERT INTO picks (user_id, game_id, pick_type, player_name, player_position, odds, stake)
VALUES (1, 42, 'FTD', 'Christian McCaffrey', 'RB', 500, 1.0);
```

### bankroll_history

Historical snapshots of user bankrolls (for charts).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | Unique identifier |
| user_id | INTEGER | FK → users.id | User |
| week | INTEGER | NOT NULL | Week number |
| season | INTEGER | NOT NULL | Season year |
| bankroll | DECIMAL(10,2) | NOT NULL | Bankroll amount |
| recorded_at | DATETIME | DEFAULT NOW | Snapshot time |

**Example:**
```sql
INSERT INTO bankroll_history (user_id, week, season, bankroll)
VALUES (1, 13, 2025, 18.50);
```

### match_decisions

Manual grading overrides for disputed results.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | Unique identifier |
| pick_id | INTEGER | FK → picks.id | Pick being overridden |
| decision | VARCHAR(10) | NOT NULL | "W", "L", or "P" |
| reason | TEXT | NULLABLE | Why override was made |
| decided_by | VARCHAR(50) | NULLABLE | Admin username |
| decided_at | DATETIME | DEFAULT NOW | Override timestamp |

## Migrations

### Migration System

We use **Flask-Migrate** (Alembic) for database version control.

**Migration Files Location:**
```
migrations/
├── alembic.ini             # Alembic config
├── env.py                  # Migration environment
├── script.py.mako          # Migration template
└── versions/               # Migration scripts
    └── 66a861c9f537_initial_migration.py
```

### Common Migration Commands

```bash
# Initialize migrations (already done)
flask db init

# Create new migration after model changes
flask db migrate -m "Add new column to users"

# Review generated migration
cat migrations/versions/<hash>_add_new_column.py

# Apply migration
flask db upgrade

# Rollback one migration
flask db downgrade

# Show current version
flask db current

# Show migration history
flask db history
```

### Example Migration Workflow

1. **Modify model:**

```python
# app/models.py
class User(db.Model):
    # Add new column
    phone_number = db.Column(db.String(20), nullable=True)
```

2. **Generate migration:**

```bash
flask db migrate -m "Add phone number to users"
```

3. **Review generated file:**

```python
# migrations/versions/abc123_add_phone_number.py
def upgrade():
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))

def downgrade():
    op.drop_column('users', 'phone_number')
```

4. **Apply migration:**

```bash
flask db upgrade
```

### Manual Migrations

For complex changes, create empty migration:

```bash
flask db revision -m "Complex data transformation"
```

Edit the file manually:

```python
def upgrade():
    # Custom SQL or Python logic
    connection = op.get_bind()
    connection.execute(
        "UPDATE picks SET result = 'P' WHERE result IS NULL AND graded_at IS NOT NULL"
    )

def downgrade():
    pass  # Or reverse operation
```

## Data Management

### Importing NFL Data

```bash
# Import current season schedule
curl -X POST http://localhost:5000/api/import-data \
  -H "Content-Type: application/json" \
  -d '{"season": 2025}'
```

### Grading Picks

```bash
# Auto-grade a week
curl -X POST http://localhost:5000/api/grade-week \
  -H "Content-Type: application/json" \
  -d '{"week": 13, "season": 2025}'
```

### Manual Data Entry

```python
from app import create_app, db
from app.models import User, Game, Pick

app = create_app()
with app.app_context():
    # Create user
    user = User(username='newuser', display_name='New User')
    db.session.add(user)
    db.session.commit()
    
    # Create game
    game = Game(
        game_id='2025_14_SF_SEA',
        season=2025,
        week=14,
        home_team='SEA',
        away_team='SF',
        game_date='2025-12-05',
        game_time='20:15:00'
    )
    db.session.add(game)
    db.session.commit()
    
    # Create pick
    pick = Pick(
        user_id=user.id,
        game_id=game.id,
        pick_type='FTD',
        player_name='Christian McCaffrey',
        player_position='RB',
        odds=500,
        stake=1.0
    )
    db.session.add(pick)
    db.session.commit()
```

### Backup & Restore

**Backup:**
```bash
# SQLite (copy file)
cp instance/league.db instance/league_backup_2025-11-30.db

# Or export SQL
sqlite3 instance/league.db .dump > backup.sql
```

**Restore:**
```bash
# SQLite (replace file)
cp instance/league_backup_2025-11-30.db instance/league.db

# Or import SQL
sqlite3 instance/league.db < backup.sql
```

### Data Cleanup

```python
# Remove test data
from app import create_app, db
from app.models import Pick

app = create_app()
with app.app_context():
    # Delete all ungraded picks from week 1
    Pick.query.filter_by(week=1, result=None).delete()
    db.session.commit()
```

## Query Examples

### Get User Standings

```python
from app.services import StatsService
standings = StatsService.calculate_standings(season=2025)
```

### Get All Picks for a Week

```python
picks = Pick.query.join(Game).filter(
    Game.season == 2025,
    Game.week == 13
).all()
```

### Get User Pick History

```python
user_picks = Pick.query.filter_by(user_id=1).join(Game).order_by(
    Game.week.desc()
).all()
```

### Get Ungraded Picks

```python
ungraded = Pick.query.filter(
    Pick.result.is_(None),
    Pick.graded_at.is_(None)
).all()
```

## Performance Considerations

### Indexes

Current indexes are on:
- `users.username` (unique constraint)
- `games.game_id` (unique constraint)
- `games.(season, week)` (composite)
- `picks.(user_id, game_id, pick_type)` (unique constraint)
- `picks.user_id` (foreign key)
- `picks.game_id` (foreign key)

### Query Optimization

**Use eager loading to avoid N+1:**

```python
# Bad (N+1 queries)
picks = Pick.query.all()
for pick in picks:
    print(pick.user.username)  # Separate query per pick

# Good (1 query)
from sqlalchemy.orm import joinedload
picks = Pick.query.options(joinedload(Pick.user)).all()
for pick in picks:
    print(pick.user.username)  # No additional queries
```

**Limit result sets:**

```python
# Get only recent picks
recent_picks = Pick.query.order_by(Pick.created_at.desc()).limit(50).all()
```

### Connection Pooling

Configured in `app/config.py`:

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,          # Max connections
    'pool_recycle': 3600,     # Recycle after 1 hour
    'pool_pre_ping': True,    # Verify connection before use
}
```

## Production Database

### PostgreSQL Setup

1. **Install PostgreSQL** (Heroku, AWS RDS, or local)

2. **Update environment variable:**

```env
DATABASE_URL=postgresql://user:password@localhost:5432/league_db
```

3. **Run migrations:**

```bash
flask db upgrade
```

### Differences from SQLite

- **Concurrent writes:** PostgreSQL handles better
- **Data types:** More strict type checking
- **Performance:** Better for large datasets
- **Full-text search:** Native support
- **JSON columns:** Better JSON support

### Migration from SQLite to PostgreSQL

```bash
# Export SQLite data
sqlite3 instance/league.db .dump > data.sql

# Import to PostgreSQL (may need manual edits)
psql -U postgres -d league_db -f data.sql
```

Or use [pgloader](https://github.com/dimitri/pgloader):

```bash
pgloader sqlite://instance/league.db postgresql://user:pass@localhost/league_db
```

## Troubleshooting

### Database Locked

```bash
# Close all connections
# Restart Flask server
# Or copy database to new file
```

### Migration Conflicts

```bash
# View current version
flask db current

# Force to specific version
flask db stamp <revision>

# Or delete migrations and start fresh
rm -rf migrations/
flask db init
flask db migrate -m "Initial migration"
```

### Corrupted Database

```bash
# Check integrity
sqlite3 instance/league.db "PRAGMA integrity_check;"

# Restore from backup
cp instance/league_backup.db instance/league.db
```

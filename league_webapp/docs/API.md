# API Reference

Complete documentation for all REST API endpoints.

## Base URL

- **Development**: `http://localhost:5000/api`
- **Production**: `https://your-domain.com/api`

## Authentication

⚠️ **Not yet implemented** - All endpoints currently public

## Endpoints

### Standings

#### Get League Standings

```http
GET /api/standings?season=2025
```

**Query Parameters:**
- `season` (int, optional): Season year (default: 2025)

**Response:**
```json
{
  "standings": [
    {
      "user_id": 1,
      "username": "Jeremy",
      "ftd_wins": 3,
      "ftd_losses": 9,
      "ftd_total": 12,
      "atts_wins": 0,
      "atts_losses": 0,
      "atts_total": 0,
      "total_bankroll": 18.50,
      "rank": 1
    }
  ],
  "season": 2025,
  "stats": {
    "total_picks": 145,
    "total_games": 111,
    "active_users": 9
  }
}
```

**Cache:** 60 seconds

---

### Picks

#### Get Picks (with filters)

```http
GET /api/picks?season=2025&week=13&user_id=1
```

**Query Parameters:**
- `season` (int, optional): Filter by season
- `week` (int, optional): Filter by week
- `user_id` (int, optional): Filter by user

**Response:**
```json
{
  "picks": [
    {
      "id": 1,
      "user_id": 1,
      "username": "Jeremy",
      "game_id": 42,
      "game_matchup": "DAL @ WSH",
      "week": 13,
      "pick_type": "FTD",
      "player_name": "Terry McLaurin",
      "player_position": "WR",
      "odds": 1400,
      "stake": 1.0,
      "result": "L",
      "payout": 0.0,
      "graded_at": "2024-11-25T10:30:00"
    }
  ]
}
```

**Cache:** 60 seconds

#### Create Pick

```http
POST /api/picks
Content-Type: application/json

{
  "user_id": 1,
  "game_id": 42,
  "pick_type": "FTD",
  "player_name": "Christian McCaffrey",
  "player_position": "RB",
  "odds": 500,
  "stake": 1.0
}
```

**Response:**
```json
{
  "message": "Pick created successfully",
  "pick_id": 146
}
```

**Status Codes:**
- `201` - Created
- `400` - Missing required fields
- `409` - Pick already exists for this user/game/type

**Cache Action:** Clears all cache

#### Update Pick

```http
PUT /api/picks/146
Content-Type: application/json

{
  "player_name": "Kyle Juszczyk",
  "odds": 2500
}
```

**Response:**
```json
{
  "message": "Pick updated successfully"
}
```

**Status Codes:**
- `200` - Updated
- `404` - Pick not found

**Cache Action:** Clears all cache

#### Delete Pick

```http
DELETE /api/picks/146
```

**Response:**
```json
{
  "message": "Pick deleted successfully"
}
```

**Status Codes:**
- `200` - Deleted
- `404` - Pick not found

**Cache Action:** Clears all cache

---

### Games & Weeks

#### Get Weekly Games

```http
GET /api/weekly-games?season=2025&week=13
```

**Query Parameters:**
- `season` (int, optional): Season year (default: 2025)
- `week` (int, optional): Week number (default: current week)

**Response:**
```json
{
  "games": [
    {
      "game_id": "2025_13_DAL_WSH",
      "week": 13,
      "gameday": "2025-11-28",
      "home_team": "WSH",
      "away_team": "DAL",
      "home_score": 24,
      "away_score": 20,
      "game_type": "REG"
    }
  ],
  "week": 13,
  "season": 2025
}
```

**Cache:** 300 seconds

#### Get Week Detail

```http
GET /api/week-detail?season=2025&week=13
```

**Query Parameters:**
- `season` (int, required): Season year
- `week` (int, required): Week number

**Response:**
```json
{
  "games": [
    {
      "game_id": "2025_13_DAL_WSH",
      "db_id": 42,
      "week": 13,
      "matchup": "DAL @ WSH",
      "home_team": "WSH",
      "away_team": "DAL",
      "game_date": "2025-11-28",
      "game_time": "16:30:00",
      "is_final": true,
      "actual_first_td_player": "Terry McLaurin",
      "ftd_picks": [
        {
          "id": 1,
          "user_id": 1,
          "username": "Jeremy",
          "player_name": "Terry McLaurin",
          "player_position": "WR",
          "odds": 1400,
          "stake": 1.0,
          "result": "W",
          "payout": 14.0,
          "graded_at": "2024-11-25T10:30:00"
        }
      ],
      "atts_picks": [],
      "total_picks": 1
    }
  ],
  "week": 13,
  "season": 2025,
  "available_weeks": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
}
```

**Cache:** 60 seconds

#### Get All Games

```http
GET /api/games?season=2025
```

**Query Parameters:**
- `season` (int, optional): Filter by season

**Response:**
```json
{
  "games": [
    {
      "id": 42,
      "game_id": "2025_13_DAL_WSH",
      "season": 2025,
      "week": 13,
      "home_team": "WSH",
      "away_team": "DAL",
      "game_date": "2025-11-28",
      "game_time": "16:30:00",
      "is_final": true,
      "actual_first_td_player": "Terry McLaurin"
    }
  ]
}
```

**Cache:** 300 seconds

---

### Users

#### Get All Users

```http
GET /api/users
```

**Response:**
```json
{
  "users": [
    {
      "id": 1,
      "username": "Jeremy",
      "display_name": "Jeremy",
      "is_active": true
    }
  ]
}
```

**Cache:** 300 seconds

#### Get User Detail

```http
GET /api/user/1?season=2025
```

**Path Parameters:**
- `user_id` (int, required): User ID

**Query Parameters:**
- `season` (int, optional): Filter picks by season

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "Jeremy",
    "display_name": "Jeremy",
    "is_active": true
  },
  "picks": [
    {
      "id": 1,
      "game_matchup": "DAL @ WSH",
      "week": 13,
      "player_name": "Terry McLaurin",
      "pick_type": "FTD",
      "odds": 1400,
      "result": "W",
      "payout": 14.0
    }
  ],
  "stats": {
    "ftd_wins": 3,
    "ftd_losses": 9,
    "atts_wins": 0,
    "atts_losses": 0,
    "total_bankroll": 18.50
  }
}
```

**Cache:** 60 seconds

---

### Analysis & Best Bets

#### Get Best Bets

```http
GET /api/best-bets?season=2025
```

**Query Parameters:**
- `season` (int, optional): Season year (default: 2025)

**Response:**
```json
{
  "bets": [
    {
      "player": "Christian McCaffrey",
      "team": "SF",
      "opponent": "SEA",
      "position": "RB",
      "prob": 8.5,
      "fair_odds": 1176,
      "best_odds": 500,
      "sportsbook": "DraftKings",
      "ev": 42.5,
      "kelly": 3.2,
      "first_tds": 2,
      "games": 5,
      "rz_opps": 8,
      "rz_tds": 3,
      "od_opps": 4,
      "od_tds": 1,
      "funnel_type": "WR",
      "game_id": "2025_14_SF_SEA"
    }
  ],
  "week": 14,
  "season": 2025,
  "last_updated": "2025-11-30T10:00:00"
}
```

**Cache:** 1800 seconds (30 minutes)

#### Get Analysis Data

```http
GET /api/analysis?season=2025
```

**Query Parameters:**
- `season` (int, optional): Season year (default: 2025)

**Response:**
```json
{
  "season": 2025,
  "player_data": [
    {
      "name": "Christian McCaffrey",
      "position": "RB",
      "team": "SF",
      "stats_full": {
        "first_tds": 5,
        "team_games": 12,
        "prob": 0.0833
      },
      "stats_recent": {
        "first_tds": 2,
        "team_games": 5
      }
    }
  ],
  "defense_data": {
    "WR_funnel": ["LAC", "KC"],
    "RB_funnel": ["SF", "BAL"],
    "TE_funnel": ["BUF"]
  },
  "error": null
}
```

**Cache:** 300 seconds

---

### Admin

#### Grade Week

```http
POST /api/grade-week
Content-Type: application/json

{
  "week": 13,
  "season": 2025
}
```

**Response:**
```json
{
  "message": "Week 13 graded successfully",
  "results": {
    "total_picks": 35,
    "wins": 5,
    "losses": 28,
    "pushes": 0,
    "pending": 2
  }
}
```

**Status Codes:**
- `200` - Success
- `400` - Missing required fields

**Cache Action:** Clears all cache

#### Import NFL Data

```http
POST /api/import-data
Content-Type: application/json

{
  "season": 2025
}
```

**Response:**
```json
{
  "message": "Data import for season 2025 successful."
}
```

**Status Codes:**
- `200` - Success
- `500` - Import failed

**Cache Action:** Clears all cache

#### Get Dashboard Stats

```http
GET /api/admin/dashboard-stats?season=2025
```

**Response:**
```json
{
  "total_users": 9,
  "active_users": 9,
  "total_picks": 145,
  "total_games": 111,
  "weeks_completed": 13,
  "season": 2025
}
```

**Cache:** 60 seconds

---

## Error Responses

All errors return JSON with the following structure:

```json
{
  "error": "Error message description"
}
```

**Common Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request (missing/invalid parameters)
- `404` - Not Found
- `409` - Conflict (duplicate resource)
- `500` - Internal Server Error

## Rate Limiting

⚠️ **Not yet implemented** - No rate limits currently

## Response Headers

All responses include:
- `Content-Type: application/json`
- `X-Response-Time: <duration>s` (e.g., "0.045s")
- `Access-Control-Allow-Origin: http://localhost:3000`

## Caching

Responses are cached with the following TTLs:

| Endpoint | Cache Duration |
|----------|----------------|
| `/api/standings` | 60 seconds |
| `/api/best-bets` | 1800 seconds |
| `/api/analysis` | 300 seconds |
| `/api/weekly-games` | 300 seconds |
| `/api/week-detail` | 60 seconds |
| `/api/picks` | 60 seconds |
| `/api/users` | 300 seconds |
| `/api/games` | 300 seconds |
| `/api/user/<id>` | 60 seconds |

Cache is cleared on any POST/PUT/DELETE operation.

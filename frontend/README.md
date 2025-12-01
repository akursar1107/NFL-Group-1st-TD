# NFL First TD League React Frontend

## Project Overview
This is the React frontend for the NFL First TD League web application. It connects to a Python/Flask backend and provides a modern, responsive UI for league management, analytics, and betting tools.

## Features
- Real-time standings and leaderboard
- Best Bets scanner (EV, Kelly, matchup, recent form)
- Analysis dashboard (player stats, defense rankings, trends)
- Weekly games and picks view
- Authentication (login/logout, password management)
- Admin tools (pick management, grading, match review)
- Bulk pick import via CSV
- User profiles and multi-league support
- Export features (CSV/PDF)
- Mobile responsiveness and navigation
- Achievements/badges

## Project Structure
```
frontend/
  public/           # Static assets (favicon, manifest, images)
  src/
    api/            # API service layer
    components/     # React components
    utils/          # TypeScript utilities (odds, stats, fuzzy match)
    assets/         # Component-level images/icons
    App.tsx         # Main app component
    index.tsx       # Entry point
  .env              # Environment variables
  README.md         # This file
```

## Environment & Config
- API base URL: Set in `.env` as `REACT_APP_API_BASE_URL`
- Odds API key: Set in `.env` as `REACT_APP_ODDS_API_KEY`
- Secret key: Set in `.env` as `REACT_APP_SECRET_KEY`

## Backend Integration
- Ensure CORS is enabled on the Flask backend for API requests from the frontend.
- Authentication is handled via session or JWT (update API service as needed).

## Development
1. Install dependencies:
   ```
   npm install
   ```
2. Start the development server:
   ```
   npm start
   ```
3. Update `.env` with your backend API URL and keys.

## Testing
- Run tests with:
  ```
  npm test
  ```

## Deployment
- Build for production:
  ```
  npm run build
  ```
- Deploy the `build/` directory to your hosting provider.

## Documentation
- See `future_state.md` in your notes for migration strategy and planning.
- Update this README as new features/components are added.

---

**Contact:** For issues or feature requests, use the main project repository.

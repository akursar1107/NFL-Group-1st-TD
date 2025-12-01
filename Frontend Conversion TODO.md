# Frontend Conversion TODO

## Goal
Migrate from dual Flask templates + React frontend to a **React-only frontend** with **Flask API-only backend**.

---

## Current Architecture Issues
- **Double maintenance**: Every feature built twice (Flask templates + React components)
- **Inconsistency**: Changes to one don't automatically reflect in the other
- **Confusion**: Two different URLs serving similar content (localhost:5000 vs localhost:3000)
- **Wasted effort**: Duplicate code and logic

---

## Target Architecture
- **Frontend**: React app (localhost:3000) - All UI, routing, and user interactions
- **Backend**: Flask API (localhost:5000/api/*) - Data endpoints only, no HTML rendering
- **Deployment**: Flask serves React build in production, all routes go through single domain

---

## Phase 1: Assessment ✅ (Start Here)

### Current Pages Inventory
- [ ] Audit all Flask template pages in `league_webapp/app/templates/`
- [ ] Audit all React pages in `frontend/src/pages/`
- [ ] Document which pages exist in both vs. one or the other

**Known Pages:**
- Standings
- Best Bets
- Analysis (has both Flask template AND React component)
- Weekly Games
- Week Detail
- New Pick
- All Picks
- Admin Dashboard
- Login/Profile

### API Endpoints Inventory
- [ ] List all existing `/api/*` endpoints in Flask
- [ ] Document what data each endpoint returns
- [ ] Identify which pages need new API endpoints

---

## Phase 2: Build Missing React Pages

### Priority 1: Authentication & Core Pages
- [ ] **Login Page** (`frontend/src/pages/Login.tsx`)
  - Create API endpoint: `POST /api/auth/login`
  - Create API endpoint: `POST /api/auth/logout`
  - Create API endpoint: `GET /api/auth/user`
  - Implement auth context/provider
  - Store JWT/session token
  
- [ ] **Standings Page** (`frontend/src/pages/Standings.tsx`)
  - Create API endpoint: `GET /api/standings`
  - Display league standings table
  - Match Flask template functionality

- [ ] **Profile Page** (`frontend/src/pages/Profile.tsx`)
  - Create API endpoint: `GET /api/profile`
  - Create API endpoint: `PUT /api/profile`
  - User info display and editing

### Priority 2: Game & Pick Management
- [ ] **Weekly Games Page** (`frontend/src/pages/WeeklyGames.tsx`)
  - Create API endpoint: `GET /api/weekly-games`
  - Game schedule display
  - Week navigation

- [ ] **Week Detail Page** (`frontend/src/pages/WeekDetail.tsx`)
  - Create API endpoint: `GET /api/week/:weekNum`
  - Detailed week view
  - Picks for specific week

- [ ] **New Pick Page** (`frontend/src/pages/NewPick.tsx`)
  - Create API endpoint: `POST /api/picks`
  - Form for submitting picks
  - Validation and error handling

- [ ] **All Picks Page** (`frontend/src/pages/AllPicks.tsx`)
  - Create API endpoint: `GET /api/picks`
  - Already exists? Verify functionality
  - Filter and sort picks

### Priority 3: Admin & Analysis
- [ ] **Best Bets Page** (`frontend/src/pages/BestBets.tsx`)
  - Create API endpoint: `GET /api/best-bets`
  - Display betting recommendations
  - Match Flask functionality

- [ ] **Analysis Page** (`frontend/src/pages/Analysis.tsx`)
  - ✅ Already exists
  - ✅ API endpoint exists: `GET /api/analysis`
  - [ ] Verify all tabs work correctly
  - [ ] Fix any styling issues

- [ ] **Admin Dashboard** (`frontend/src/pages/Admin.tsx`)
  - Create API endpoint: `GET /api/admin/dashboard`
  - Admin-only route protection
  - Management tools

---

## Phase 3: Authentication & Session Management

### Auth System Setup
- [ ] Choose auth strategy (JWT vs. session-based)
- [ ] Create auth context in React (`frontend/src/context/AuthContext.tsx`)
- [ ] Implement login flow
- [ ] Implement logout flow
- [ ] Add auth state persistence (localStorage/cookies)
- [ ] Create protected route wrapper component

### API Auth Integration
- [ ] Add auth headers to all API requests
- [ ] Handle 401 Unauthorized responses
- [ ] Implement token refresh (if using JWT)
- [ ] Add CORS configuration for auth cookies

---

## Phase 4: API Endpoints - Complete List

### Authentication
- [ ] `POST /api/auth/login` - User login
- [ ] `POST /api/auth/logout` - User logout
- [ ] `GET /api/auth/user` - Get current user info
- [ ] `POST /api/auth/register` - New user registration (if needed)

### Standings & Users
- [ ] `GET /api/standings` - League standings
- [ ] `GET /api/users` - List all users
- [ ] `GET /api/users/:id` - Get user details
- [ ] `GET /api/profile` - Current user profile
- [ ] `PUT /api/profile` - Update user profile

### Games & Weeks
- [ ] `GET /api/weekly-games` - Games for current week
- [ ] `GET /api/weekly-games?week=:num` - Games for specific week
- [ ] `GET /api/week/:weekNum` - Week details
- [ ] `GET /api/schedule` - Full season schedule

### Picks
- [ ] `GET /api/picks` - All picks (with filters)
- [ ] `GET /api/picks/:id` - Single pick details
- [ ] `POST /api/picks` - Create new pick
- [ ] `PUT /api/picks/:id` - Update pick
- [ ] `DELETE /api/picks/:id` - Delete pick
- [ ] `GET /api/picks/user/:userId` - User's picks

### Analysis & Stats
- [ ] ✅ `GET /api/analysis` - Analysis data (already exists)
- [ ] `GET /api/best-bets` - Best betting opportunities
- [ ] `GET /api/player-stats` - Player statistics
- [ ] `GET /api/team-stats` - Team statistics

### Admin
- [ ] `POST /api/admin/grade-week` - Grade a week's picks
- [ ] `GET /api/admin/dashboard` - Admin dashboard data
- [ ] `GET /api/admin/all-picks` - Admin view of all picks
- [ ] `PUT /api/admin/users/:id` - Manage users

---

## Phase 5: React Router Setup

### Install & Configure React Router
- [ ] Install: `npm install react-router-dom`
- [ ] Create router configuration in `App.tsx`
- [ ] Set up route protection for auth-required pages
- [ ] Set up admin-only routes

### Route Structure
```
/                    → Standings (home)
/login               → Login
/profile             → Profile
/best-bets           → Best Bets
/analysis            → Analysis
/weekly-games        → Weekly Games
/week/:num           → Week Detail
/picks/new           → New Pick
/picks/all           → All Picks
/admin               → Admin Dashboard (protected)
/admin/picks         → Admin All Picks (protected)
```

### Navigation Component
- [ ] Create main navigation component
- [ ] Show/hide links based on auth state
- [ ] Show/hide admin links based on user role
- [ ] Active route highlighting

---

## Phase 6: Deployment Configuration

### Development Setup
- [ ] Verify CORS settings for localhost:3000 → localhost:5000
- [ ] Update `REACT_APP_API_BASE_URL` environment variable
- [ ] Test all API calls from React to Flask

### Production Setup
- [ ] Configure Flask to serve React build files
- [ ] Set up production build process: `npm run build`
- [ ] Update Flask routes to serve `index.html` for all non-API routes
- [ ] Configure proper CORS for production domain
- [ ] Update Docker configuration for production deployment

### Flask Configuration Changes
- [ ] Remove HTML template routes (keep only `/api/*`)
- [ ] Add route to serve React build: `app.static_folder = 'frontend/build'`
- [ ] Add catch-all route: `@app.route('/', defaults={'path': ''})`
- [ ] Keep only API blueprint routes

---

## Phase 7: Testing & Cutover

### Testing Checklist
- [ ] Test all React pages load correctly
- [ ] Test all forms submit successfully
- [ ] Test authentication flow (login/logout)
- [ ] Test protected routes redirect to login
- [ ] Test admin routes blocked for non-admins
- [ ] Test all API endpoints return correct data
- [ ] Test error handling and loading states
- [ ] Cross-browser testing (Chrome, Firefox, Safari, Edge)
- [ ] Mobile responsive testing

### Feature Parity Check
- [ ] Compare each React page with Flask template equivalent
- [ ] Verify all Flask features exist in React version
- [ ] Document any intentional differences
- [ ] Get user feedback on React versions

### Cutover Plan
- [ ] Archive Flask templates (move to `archive/old_templates/`)
- [ ] Update main entry point to redirect to React app
- [ ] Monitor error logs for issues
- [ ] Keep Flask templates available for rollback (don't delete)

---

## Phase 8: Cleanup (After Successful Cutover)

### Code Cleanup
- [ ] Remove unused Flask template files
- [ ] Remove Flask template routes from blueprints
- [ ] Remove template-specific Flask code
- [ ] Update Flask `__init__.py` to remove template config
- [ ] Clean up unused static assets

### Documentation Updates
- [ ] Update README with new architecture
- [ ] Document API endpoints
- [ ] Update deployment instructions
- [ ] Update development setup guide
- [ ] Add API documentation (consider Swagger/OpenAPI)

### Performance Optimization
- [ ] Implement React code splitting
- [ ] Add loading states and skeletons
- [ ] Optimize bundle size
- [ ] Add caching strategies
- [ ] Consider adding React Query for data fetching

---

## Time Estimates

**Phase 1 (Assessment)**: 1-2 days  
**Phase 2 (Build Pages)**: 1-2 weeks  
**Phase 3 (Auth)**: 2-3 days  
**Phase 4 (API Endpoints)**: 1 week  
**Phase 5 (Routing)**: 1-2 days  
**Phase 6 (Deployment)**: 2-3 days  
**Phase 7 (Testing)**: 3-5 days  
**Phase 8 (Cleanup)**: 1-2 days  

**Total Estimate**: 3-4 weeks

---

## Success Criteria

- [ ] All functionality from Flask templates replicated in React
- [ ] Users access only React frontend (localhost:3000 or production domain)
- [ ] Flask serves ONLY API endpoints (no HTML rendering)
- [ ] Authentication works seamlessly
- [ ] No broken features or regressions
- [ ] Performance is acceptable (page loads < 2 seconds)
- [ ] Mobile responsive on all pages
- [ ] Zero template maintenance (one codebase for UI)

---

## Rollback Plan

If issues arise:
1. Revert main entry point to Flask templates
2. Keep Flask template routes active during migration
3. Gradually switch pages one at a time
4. Keep both systems running until React is fully stable

---

## Notes & Considerations

- **Incremental Migration**: Can migrate page-by-page instead of all at once
- **Dual System Period**: Keep both Flask and React running during transition
- **User Communication**: Notify users of upcoming changes
- **Database**: No changes needed - Flask API uses same database
- **Sessions**: May need to update session handling for API-based auth
- **File Uploads**: Verify file upload handling in React (if applicable)

---

## Next Steps

1. ✅ Create this TODO document
2. Start Phase 1: Complete assessment of existing pages and APIs
3. Prioritize which pages to migrate first
4. Set up authentication infrastructure
5. Begin building missing React pages

**Status**: Planning Phase  
**Last Updated**: December 1, 2025

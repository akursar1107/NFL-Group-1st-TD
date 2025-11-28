# Scripts Directory

This directory contains utility scripts for database management, testing, and maintenance.

## 📁 Directory Structure

### `setup/` - One-time Setup & Maintenance Scripts

Scripts used during initial setup or major database operations:

- **`init_db.py`** - Initialize fresh database with schema and test data
  - Creates all tables (users, games, picks, bankroll_history)
  - Seeds 7 league users
  - Creates sample Week 13 game and picks
  - **Usage:** `python scripts/setup/init_db.py`

- **`reset_db.py`** - Reset database (destructive operation)
  - Drops all tables and data
  - Recreates schema
  - Re-seeds league users only
  - **Usage:** `python scripts/setup/reset_db.py` (requires confirmation)

- **`add_user.py`** - Add a single user to the database
  - Interactive or command-line usage
  - Auto-generates email if not provided
  - **Usage:** `python scripts/setup/add_user.py [username] [email] [display_name]`

- **`add_missing_week13_games.py`** - One-time fix for missing Week 13 games
  - Added DEN @ WAS and NYG @ NE games
  - **Status:** Completed, kept for reference

---

### `testing/` - Diagnostic & Verification Scripts

Scripts for debugging, testing features, and verifying data integrity:

- **`test_atts_grading.py`** - Test ATTS (Anytime TD) grading logic
  - Loads Week 2 data
  - Shows all TD scorers for games
  - Useful for debugging ATTS grading functionality

- **`check_pending.py`** - Display all pending picks
  - Shows current NFL week
  - Lists pending picks by week
  - **Usage:** `python scripts/testing/check_pending.py`

- **`check_picks.py`** - Quick FTD/ATTS pick count verification
  - Shows total FTD and ATTS picks
  - Displays sample ATTS picks

- **`check_week13_schedule.py`** - Verify Week 13 schedule data
  - Fetches Week 13 games from nflreadpy
  - Useful for comparing database vs source data

- **`verify_grading.py`** - Verify grading results for a specific week
  - Shows Week 13 picks with results and payouts
  - Displays remaining pending picks by week
  - **Usage:** `python scripts/testing/verify_grading.py`

- **`verify_import.py`** - Comprehensive database verification
  - User summary with pick counts and records
  - Games by week breakdown
  - Pick results summary (wins/losses/pending)
  - Sample picks display
  - **Usage:** `python scripts/testing/verify_import.py`

---

## 🔧 Production Scripts (Root Directory)

These scripts remain in the root directory for easy access during normal operations:

- **`auto_grade.py`** - Automated weekly grading (scheduled task)
- **`grade_week.py`** - Manual grading for specific weeks
- **`import_csv.py`** - Import historical picks from CSV files

---

## 📝 Notes

- All scripts assume they're run from the `league_webapp` root directory
- Scripts automatically create Flask app context for database access
- Testing scripts are read-only and safe to run anytime
- Setup scripts (especially `reset_db.py`) are destructive - use with caution

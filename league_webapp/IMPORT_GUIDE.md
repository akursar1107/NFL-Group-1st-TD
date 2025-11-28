# Database Reset and CSV Import Guide

## Step 1: Reset Database

This will delete ALL existing data (games, picks, results) and start fresh:

```powershell
python reset_db.py
```

**You will be prompted to confirm** by typing `YES`. The script will:
- Drop all database tables
- Recreate the schema
- Re-seed the 7 league users (Phil, Anders, Neil, Dan C, Tony, Luke, Jeremy)

## Step 2: Import CSV Data

This will import historical picks from the CSV file with interactive validation:

```powershell
python import_csv.py
```

### Interactive Prompts

During import, you may be asked to clarify ambiguous data:

#### Unknown Team Names
```
⚠️  Unknown team name: 'San Francisco'
Enter team abbreviation (e.g., 'DAL', 'PHI') or press Enter to skip:
> SF
```

#### Games Not Found in Schedule
```
⚠️  Game not found in NFL schedule:
   Week 13: GB @ DET
   Expected game_id: 2025_13_GB_DET

Options:
  1. Enter correct game_id manually
  2. Create minimal record with this game_id
  3. Skip this game
Select option (1-3): 2
```

#### Suspicious Player Names
```
⚠️  Suspicious player name on row 45: 'J'
   Week 5: BUF @ HOU
   Picker: Phil
Use this player name anyway? (y/n): n
Enter corrected player name (or press Enter to skip): Josh Allen
```

### Import Log

All decisions are logged to `import_log.txt` with timestamps:
```
[2025-11-28 14:32:15] Team mapping: 'San Francisco' -> 'SF' (user confirmed)
[2025-11-28 14:32:28] Game created: 2025_13_GB_DET (not in schedule, user confirmed minimal record)
[2025-11-28 14:32:45] Player name: Row 45 'J' -> 'Josh Allen' (user corrected)
```

## Step 3: Verify Import

Check the database after import:

```powershell
python verify_import.py
```

## Step 4: Grade Picks (Optional)

If you want to auto-grade picks after import, start the web app and use the "Grade All Weeks" button, or run the CLI grading script.

## Troubleshooting

- **Import fails mid-way**: Check `import_log.txt` to see where it stopped. Fix the CSV row and re-run (already imported data will be skipped due to duplicate checks).
- **Wrong team mapping**: Edit the `TEAM_MAP` dictionary in `import_csv.py` before running.
- **Need to re-import**: Run `reset_db.py` again to start completely fresh.

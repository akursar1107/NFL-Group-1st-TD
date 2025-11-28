# firstTD_CLI - File Structure Optimization

## ✅ Optimized Structure

```
firstTD_CLI/
├── archive/                      # 📦 Archived old versions
│   ├── getOdds_old.py           # Old odds fetching (1374 lines, hardcoded API key)
│   └── OLD_getOdds.py           # Older odds fetching (209 lines, hardcoded API key)
├── cache/                        # 🗄️ Generated data cache
│   ├── odds/                    # Real-time odds cache (JSON files)
│   ├── season_2025_pbp.parquet  # Play-by-play data
│   ├── season_2025_roster.parquet
│   └── season_2025_schedule.parquet
├── config.py                     # ✅ Configuration (API key from env)
├── data.py                       # ✅ Core: NFL data loading & caching
├── stats.py                      # ✅ Core: First TD statistics & analysis
├── odds.py                       # ✅ Core: Odds API integration
├── ui.py                         # ✅ Core: Terminal UI & display functions
├── main.py                       # ✅ Application entry point
├── test_scanner.py              # ✅ Testing: Scanner functionality test
├── README.md                     # ✅ Documentation
├── requirements.txt              # ✅ Dependencies
├── .gitignore                    # ✅ Git configuration
├── instance/                     # (generated, ignore)
└── __pycache__/                  # (generated, ignore)
```

---

## 📋 Changes Made

### **Archived (moved to archive/):**
- ❌ `getOdds_old.py` (1374 lines) - Superseded by `odds.py`
  - Contains hardcoded API key `11d265853d712ded110d5e0a5ff82c5b`
  - Replaced by modular `odds.py` + `config.py`
  
- ❌ `OLD_getOdds.py` (209 lines) - Early prototype
  - Also has hardcoded API key
  - Very basic implementation, no longer used

### **Core Files (kept in root):**
- ✅ `config.py` - API key from environment variable
- ✅ `data.py` - NFL data loading with caching
- ✅ `stats.py` - First TD statistics engine
- ✅ `odds.py` - Current odds API integration
- ✅ `ui.py` - Terminal UI display functions
- ✅ `main.py` - Interactive CLI application
- ✅ `test_scanner.py` - Test best bets scanner

---

## 🔒 Security Improvement

**Before:** API keys hardcoded in old files  
**After:** API key loaded from environment variable in `config.py`

Old files should be deleted or kept in archive with API keys removed.

---

## 🗑️ Cleanup Commands

```powershell
cd 'C:\Users\akurs\Desktop\Vibe Coder\main\firstTD_CLI'

# Move old files to archive
Move-Item getOdds_old.py archive\
Move-Item OLD_getOdds.py archive\

# Verify structure
Get-ChildItem -Name
```

---

## 📊 File Purpose Summary

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `config.py` | ~10 | API configuration | ✅ Active |
| `data.py` | ~200 | Load/cache NFL data | ✅ Active |
| `stats.py` | ~500 | TD statistics & analysis | ✅ Active |
| `odds.py` | ~300 | Fetch real-time odds | ✅ Active |
| `ui.py` | ~400 | Terminal UI & formatting | ✅ Active |
| `main.py` | ~800 | Main CLI application | ✅ Active |
| `test_scanner.py` | ~40 | Test scanner function | ✅ Active |
| `getOdds_old.py` | 1374 | Old odds implementation | 📦 Archive |
| `OLD_getOdds.py` | 209 | Older prototype | 📦 Archive |

---

## ⚠️ Important Notes

1. **API Key Security**: Old files contain exposed API key. Either:
   - Delete them permanently, or
   - Remove API keys before committing to Git

2. **No Breaking Changes**: Moving old files to archive won't break anything - they're not imported by any active code

3. **Cache Files**: The `cache/` directory should be in `.gitignore` (already configured)

---

## 🎯 Result

- **Root directory**: Only active, production files
- **Archive**: Old implementations preserved for reference
- **Security**: No hardcoded API keys in active code
- **Clean**: Easy to navigate and understand structure

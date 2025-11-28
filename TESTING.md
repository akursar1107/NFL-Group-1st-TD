# Testing Guide

## Installation

Install test dependencies:
```powershell
pip install -r requirements-dev.txt
```

## Running Tests

**Run all tests:**
```powershell
pytest
```

**Run specific test file:**
```powershell
pytest tests/test_nfl_core/test_stats.py
```

**Run specific test:**
```powershell
pytest tests/test_webapp/test_models.py::TestUserModel::test_create_user
```

**Run with coverage:**
```powershell
pytest --cov=nfl_core --cov=league_webapp/app
```

**View HTML coverage report:**
```powershell
pytest --cov=nfl_core --cov=league_webapp/app --cov-report=html
# Open htmlcov/index.html in browser
```

**Run verbose:**
```powershell
pytest -v
```

**Run only fast tests (skip slow network tests):**
```powershell
pytest -m "not slow"
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_nfl_core/
│   ├── test_stats.py        # Statistics calculations
│   └── test_data.py         # Data loading
├── test_cli/
│   └── (future CLI tests)
└── test_webapp/
    ├── test_models.py       # Database models
    ├── test_routes.py       # Flask routes
    └── test_grading.py      # Pick grading logic
```

## Writing Tests

Use pytest fixtures from `conftest.py`:

```python
def test_example(app, client, sample_user):
    """Test using fixtures"""
    with app.app_context():
        # Test code here
        pass
```

Available fixtures:
- `app` - Flask test app with in-memory database
- `client` - Test client for HTTP requests
- `sample_user` - Pre-created test user
- `sample_game` - Pre-created test game
- `sample_pick` - Pre-created test pick

## CI Integration

Tests run automatically on GitHub push/PR via GitHub Actions.

See `.github/workflows/tests.yml` for configuration.

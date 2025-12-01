# Docker Setup for NFL First TD App

## Quick Start

1. **Start both services:**
   ```powershell
   cd docker
   docker-compose up
   ```

2. **Access the app:**
   - React Frontend: http://localhost:3000
   - Flask Backend: http://localhost:5000

3. **Stop services:**
   ```powershell
   docker-compose down
   ```

## Commands

**Build and start (rebuild if changed):**
```powershell
docker-compose up --build
```

**Run in background (detached):**
```powershell
docker-compose up -d
```

**View logs:**
```powershell
docker-compose logs -f
docker-compose logs backend
docker-compose logs frontend
```

**Restart a service:**
```powershell
docker-compose restart backend
docker-compose restart frontend
```

**Stop and remove containers:**
```powershell
docker-compose down
```

**Remove containers and volumes:**
```powershell
docker-compose down -v
```

## Development Notes

- Code changes in `league_webapp/`, `nfl_core/`, and `frontend/src/` auto-reload
- No need to activate venv or run npm separately
- Both services run simultaneously with one command
- Volumes are mounted so changes persist

## Troubleshooting

**Port already in use:**
```powershell
# Stop other services using ports 3000 or 5000
docker-compose down
```

**Rebuild after dependency changes:**
```powershell
docker-compose up --build
```

**Clear everything and start fresh:**
```powershell
docker-compose down -v
docker system prune -a
docker-compose up --build
```

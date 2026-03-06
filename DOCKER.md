# Docker Setup for Kruzinator

This project uses Docker for both development and production deployments with Traefik as a reverse proxy.

## Prerequisites

- Docker and Docker Compose installed
- Traefik running on the external `web` network with TLS challenge configured
- Domain `dev.kruzinator.capturemyhand.com` pointing to your server

## Architecture

### Backend (kruzinator-api)
- Python FastAPI application
- Uses UV for fast dependency installation
- Multi-stage build for optimized image size
- Accessible at: `https://dev.kruzinator.capturemyhand.com/api`

### Frontend (kruzinator-vue)
- Vue 3 + TypeScript + Vite
- Multi-stage build (Node builder + Nginx runtime)
- Configured for SPA routing
- Accessible at: `https://dev.kruzinator.capturemyhand.com`

## Quick Start

### Production Build
```bash
docker compose up -d --build
```

### Development with Hot Reload
```bash
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

### Development with Watch Mode (Recommended)
Uses Docker Compose watch for automatic file syncing:
```bash
docker compose -f compose.yaml -f compose.dev.yaml watch
```

This will:
- Sync code changes instantly without rebuilding
- Automatically rebuild when dependencies change
- Provide hot reload for both frontend and backend

### Viewing Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f kruzinator-api
docker compose logs -f kruzinator-vue
```

### Stopping Services
```bash
docker compose down
```

### Rebuilding After Changes
```bash
# Backend only
docker compose up -d --build kruzinator-api

# Frontend only
docker compose up -d --build kruzinator-vue
```

## Network Configuration

### Traefik Setup
The compose file expects:
- External network named `web` (Traefik network)
- Traefik configured with TLS challenge cert resolver named `tlschallenge`
- Traefik listening on `websecure` entrypoint (typically port 443)

### Creating the Web Network
If the `web` network doesn't exist:
```bash
docker network create web
```

## Environment Variables

### Backend (Optional)
Create `kruzinator-api/.env` for environment-specific configuration:
```env
ENVIRONMENT=development
LOG_LEVEL=info
```

### Frontend (Optional)
Create `kruzinator-vue/.env` for build-time variables:
```env
VITE_API_URL=/api
```

## Health Checks

Both services include health checks:
- Backend: `GET /health`
- Frontend: Nginx health endpoint

Check service health:
```bash
docker compose ps
```

## Troubleshooting

### Port Conflicts
If you encounter port conflicts, check which services are using ports 8000 or 80:
```bash
sudo lsof -i :8000
sudo lsof -i :80
```

### Certificate Issues
If SSL certificates aren't generating:
1. Verify DNS points to your server
2. Check Traefik logs: `docker logs traefik`
3. Ensure ports 80 and 443 are accessible from the internet

### Container Not Starting
Check logs for the specific service:
```bash
docker compose logs kruzinator-api
docker compose logs kruzinator-vue
```

## Development Tips

### Backend Development
- Hot reload is enabled in development mode
- Edit files in `kruzinator-api/` and changes will auto-reload
- Access API docs at: `https://dev.kruzinator.capturemyhand.com/api/docs`

### Frontend Development
- Vite HMR (Hot Module Replacement) works in dev mode
- Edit files in `kruzinator-vue/src/` for instant updates
- Dev server runs on port 5173 inside container

### Adding Python Dependencies
1. Add to `kruzinator-api/requirements.txt`
2. Rebuild: `docker compose up -d --build kruzinator-api`

### Adding Node Dependencies
1. Add to `kruzinator-vue/package.json` or run `npm install <package>` locally
2. Rebuild: `docker compose up -d --build kruzinator-vue`

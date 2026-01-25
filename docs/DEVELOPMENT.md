```markdown
# Development Guide

## Setting Up Your Development Environment

### First Time Setup

1. **Install Docker Desktop**
   - Download from docker.com
   - Ensure Docker daemon is running

2. **Clone Repository**
```bash
git clone https://github.com/YOUR-USERNAME/cspm-compliance-dashboard.git
cd cspm-compliance-dashboard
3.	Start Services
docker-compose up -d
Daily Development Workflow
1.	Start Docker Services
docker-compose up -d
2.	View Logs
docker-compose logs -f
3.	Make Code Changes
–	Backend changes: Edit files in backend/ - auto-reloads
–	Frontend changes: Edit files in frontend/src/ - auto-reloads
4.	Stop Services
docker-compose down
Common Commands
Docker Operations
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild services after Dockerfile changes
docker-compose up -d --build

# View running containers
docker-compose ps

# View logs
docker-compose logs -f [service-name]

# Access container shell
docker exec -it cspm-backend bash
docker exec -it cspm-frontend sh
Database Operations
# Connect to PostgreSQL
docker exec -it cspm-db psql -U cspm_user -d cspm_dashboard

# Run SQL file
docker exec -i cspm-db psql -U cspm_user -d cspm_dashboard < database/schema.sql

# Backup database
docker exec cspm-db pg_dump -U cspm_user cspm_dashboard > backup.sql
Backend Operations
# Install new Python package
docker exec cspm-backend pip install package-name

# Run tests
docker exec cspm-backend pytest

# Access Python shell
docker exec -it cspm-backend python
Frontend Operations
# Install new npm package
docker exec cspm-frontend npm install package-name

# Run tests
docker exec cspm-frontend npm test
Troubleshooting
Port Already in Use
# Find process using port
lsof -i :3000  # or :8000 or :5432

# Kill process
kill -9 <PID>
Database Connection Issues
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
Service Won’t Start
# Remove all containers and volumes
docker-compose down -v

# Rebuild and start
docker-compose up -d --build

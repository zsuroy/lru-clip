# CLIP.LRU Docker Deployment

This directory contains all Docker-related files for deploying CLIP.LRU.

## Files Structure

```
docker/
├── Dockerfile                    # Main application Docker image
├── docker-compose.yml           # SQLite deployment (lightweight)
├── docker-compose.mysql.yml     # MySQL deployment (production)
├── deploy.sh                    # Deployment script
├── mysql/                       # MySQL configuration
│   └── init/
│       └── 01-init.sql          # MySQL initialization script
└── README.md                    # This file
```

## Quick Start

### Option 1: Using the deployment script (Recommended)

```bash
# Navigate to the docker directory
cd docker

# Deploy with SQLite (lightweight, good for development)
./deploy.sh sqlite

# Or deploy with MySQL (production-ready)
./deploy.sh mysql

# View logs
./deploy.sh logs

# Stop services
./deploy.sh stop

# Clear services
./deploy.sh clear

# Show service status
./deploy.sh status
```

### Option 2: Using docker-compose directly

```bash
# Navigate to the docker directory
cd docker

# For SQLite deployment
docker-compose up -d --build

# For MySQL deployment
docker-compose -f docker-compose.mysql.yml up -d --build

# Stop services
docker-compose down
# or for MySQL
docker-compose -f docker-compose.mysql.yml down
```

## Deployment Options

### SQLite Deployment (Default)
- **File**: `docker-compose.yml`
- **Database**: SQLite (file-based)
- **Use case**: Development, testing, small deployments
- **Pros**: Simple setup, no external database required
- **Cons**: Limited concurrent access, not suitable for high-traffic production

### MySQL Deployment
- **File**: `docker-compose.mysql.yml`
- **Database**: MySQL 8.0
- **Use case**: Production deployments
- **Pros**: Better performance, concurrent access, production-ready
- **Cons**: More complex setup, requires database management

## Environment Configuration

Create a `.env` file in the project root directory with your configuration:

```bash
# Security
SECRET_KEY=your-very-secure-secret-key-here

# Database (for MySQL deployment)
DB_USER=
DB_DATABASE=
DB_PASSWORD=your-app-password

# Application settings
DEBUG=false
ALLOW_ANONYMOUS=true

# File size limits (in bytes)
MAX_FILE_SIZE=104857600          # 100MB
ANONYMOUS_MAX_FILE_SIZE=10485760 # 10MB

# LRU settings
LRU_MAX_ITEMS_PER_USER=1000
LRU_CLEANUP_INTERVAL=3600
```

## Accessing the Application

After deployment, the application will be available at:

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MySQL** (if using MySQL deployment): localhost:3306

## Data Persistence

### SQLite Deployment
- Database: `../data/cliplru`
- Uploads: `../uploads/`

### MySQL Deployment
- Database: MySQL container with persistent volume
- Uploads: `../uploads/`

## Troubleshooting

### Check service status
```bash
./deploy.sh status
```

### View logs
```bash
./deploy.sh logs
```

### Restart services
```bash
./deploy.sh restart
```

### Manual container management
```bash
# List running containers
docker ps

# View specific container logs
docker logs clip-lru-app
docker logs clip-lru-mysql  # for MySQL deployment

# Execute commands in container
docker exec -it clip-lru-app bash
```

## Development

For development with live code reloading, you might want to mount the source code:

```yaml
# Add this to the app service volumes in docker-compose.yml
volumes:
  - ../app:/app/app:ro  # Mount source code (read-only)
```

## Security Notes

1. **Change default passwords** in production
2. **Use strong SECRET_KEY** for JWT tokens
3. **Configure firewall** to restrict database access
4. **Use HTTPS** in production (consider adding nginx reverse proxy)
5. **Regular backups** of database and uploads

## Backup and Restore

### SQLite Backup
```bash
# Backup database
cp data/cliplru backup/clips_$(date +%Y%m%d_%H%M%S).db

# Backup uploads
tar -czf backup/uploads_$(date +%Y%m%d_%H%M%S).tar.gz uploads/
```

### MySQL Backup
```bash
# Backup database
docker exec clip-lru-mysql mysqldump -u root -p cliplru > backup/cliplru_$(date +%Y%m%d_%H%M%S).sql

# Backup uploads (same as SQLite)
tar -czf backup/uploads_$(date +%Y%m%d_%H%M%S).tar.gz uploads/
```

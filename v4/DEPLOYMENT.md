# Deployment Guide

This guide covers deploying the Intelligent Document QA System in various environments.

## Table of Contents

1. [Local Development](#local-development)
2. [Production Deployment](#production-deployment)
3. [Environment Variables](#environment-variables)
4. [Database Setup](#database-setup)
5. [Troubleshooting](#troubleshooting)

## Local Development

### Prerequisites

- Docker Desktop 20.10+
- Docker Compose 2.0+
- Google API Key (Gemini)
- 8GB RAM minimum
- 20GB free disk space

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd intelligent-doc-qa
   ```

2. **Configure environment**
   ```bash
   cp backend/.env.example backend/.env
   ```
   
   Edit `backend/.env` and add:
   ```env
   GOOGLE_API_KEY=your-api-key-here
   ```

3. **Start services**
   ```bash
   ./start.sh
   ```
   
   Or manually:
   ```bash
   docker-compose up --build
   ```

4. **Create admin user**
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

5. **Access application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Admin: http://localhost:8000/admin

### Development Workflow

**Backend development**:
```bash
# Enter backend container
docker-compose exec backend bash

# Run tests
pytest

# Run linters
black .
isort .
flake8

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

**Frontend development**:
```bash
# Enter frontend container
docker-compose exec frontend sh

# Install new package
npm install <package-name>

# Run tests
npm test
```

**View logs**:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

## Production Deployment

### Option 1: Docker Compose (Simple Production)

For small to medium deployments on a single server.

1. **Prepare server**
   - Ubuntu 22.04 LTS recommended
   - Docker and Docker Compose installed
   - Domain name configured
   - SSL certificate (Let's Encrypt)

2. **Clone and configure**
   ```bash
   git clone <repository-url>
   cd intelligent-doc-qa
   cp backend/.env.example backend/.env
   ```

3. **Update environment for production**
   ```env
   DEBUG=False
   SECRET_KEY=<generate-strong-secret-key>
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   
   DB_NAME=docqa_prod
   DB_USER=docqa_prod
   DB_PASSWORD=<strong-password>
   
   GOOGLE_API_KEY=<your-api-key>
   
   CORS_ALLOW_ALL_ORIGINS=False
   CORS_ALLOWED_ORIGINS=https://yourdomain.com
   ```

4. **Create production docker-compose**
   ```yaml
   # docker-compose.prod.yml
   version: '3.8'
   
   services:
     db:
       image: pgvector/pgvector:pg16
       restart: always
       environment:
         POSTGRES_DB: ${DB_NAME}
         POSTGRES_USER: ${DB_USER}
         POSTGRES_PASSWORD: ${DB_PASSWORD}
       volumes:
         - postgres_data:/var/lib/postgresql/data
       networks:
         - app-network
     
     backend:
       build:
         context: ./backend
         dockerfile: Dockerfile.prod
       restart: always
       command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
       volumes:
         - media_files:/app/media
         - static_files:/app/staticfiles
       environment:
         - DEBUG=False
         - SECRET_KEY=${SECRET_KEY}
         - DB_HOST=db
         - GOOGLE_API_KEY=${GOOGLE_API_KEY}
       depends_on:
         - db
       networks:
         - app-network
     
     frontend:
       build:
         context: ./frontend
         dockerfile: Dockerfile.prod
       restart: always
       networks:
         - app-network
     
     nginx:
       image: nginx:alpine
       restart: always
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx/nginx.conf:/etc/nginx/nginx.conf
         - ./nginx/ssl:/etc/nginx/ssl
         - static_files:/var/www/static
         - media_files:/var/www/media
       depends_on:
         - backend
         - frontend
       networks:
         - app-network
   
   volumes:
     postgres_data:
     media_files:
     static_files:
   
   networks:
     app-network:
       driver: bridge
   ```

5. **Create production Dockerfiles**

   **backend/Dockerfile.prod**:
   ```dockerfile
   FROM python:3.11-slim
   
   ENV PYTHONUNBUFFERED=1
   ENV PYTHONDONTWRITEBYTECODE=1
   
   WORKDIR /app
   
   RUN apt-get update && apt-get install -y \
       gcc \
       postgresql-client \
       libpq-dev \
       && rm -rf /var/lib/apt/lists/*
   
   COPY requirements.txt /app/
   RUN pip install --upgrade pip && \
       pip install -r requirements.txt && \
       pip install gunicorn
   
   COPY . /app/
   
   RUN python manage.py collectstatic --noinput
   
   EXPOSE 8000
   
   CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
   ```

   **frontend/Dockerfile.prod**:
   ```dockerfile
   FROM node:18-alpine as build
   
   WORKDIR /app
   COPY package*.json ./
   RUN npm ci --only=production
   COPY . .
   RUN npm run build
   
   FROM nginx:alpine
   COPY --from=build /app/build /usr/share/nginx/html
   COPY nginx.conf /etc/nginx/conf.d/default.conf
   EXPOSE 80
   CMD ["nginx", "-g", "daemon off;"]
   ```

6. **Configure Nginx**

   **nginx/nginx.conf**:
   ```nginx
   upstream backend {
       server backend:8000;
   }
   
   upstream frontend {
       server frontend:80;
   }
   
   server {
       listen 80;
       server_name yourdomain.com www.yourdomain.com;
       
       # Redirect HTTP to HTTPS
       return 301 https://$server_name$request_uri;
   }
   
   server {
       listen 443 ssl http2;
       server_name yourdomain.com www.yourdomain.com;
       
       ssl_certificate /etc/nginx/ssl/cert.pem;
       ssl_certificate_key /etc/nginx/ssl/key.pem;
       
       # API requests
       location /api/ {
           proxy_pass http://backend;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       
       # Admin panel
       location /admin/ {
           proxy_pass http://backend;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       # Static files
       location /static/ {
           alias /var/www/static/;
       }
       
       # Media files
       location /media/ {
           alias /var/www/media/;
       }
       
       # Frontend
       location / {
           proxy_pass http://frontend;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

7. **Deploy**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

8. **Initialize database**
   ```bash
   docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
   docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
   ```

### Option 2: Kubernetes (Enterprise Production)

For large-scale deployments with auto-scaling.

1. **Create Kubernetes manifests** (namespace, deployments, services)
2. **Configure persistent volumes** for PostgreSQL and media files
3. **Set up Ingress** with SSL termination
4. **Configure HorizontalPodAutoscaler** for backend pods
5. **Use managed database** (e.g., AWS RDS, Google Cloud SQL)

*Detailed K8s manifests available in `/k8s` directory (to be added)*

## Environment Variables

### Required Variables

```env
# Django
SECRET_KEY=<random-50-char-string>
DEBUG=False
ALLOWED_HOSTS=your-domain.com

# Database
DB_NAME=docqa_db
DB_USER=docqa_user
DB_PASSWORD=<strong-password>
DB_HOST=db
DB_PORT=5432

# Google API
GOOGLE_API_KEY=<your-gemini-api-key>
```

### Optional Variables

```env
# Document Processing
MAX_FILE_SIZE=104857600  # 100MB
CHUNK_SIZE=800
CHUNK_OVERLAP=200

# Retrieval
TOP_K_RETRIEVAL=5
SIMILARITY_THRESHOLD=0.7

# CORS
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

## Database Setup

### PostgreSQL with pgvector

1. **Verify pgvector extension**
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```

2. **Create extension if needed**
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

3. **Backup database**
   ```bash
   docker-compose exec db pg_dump -U docqa_user docqa_db > backup.sql
   ```

4. **Restore database**
   ```bash
   docker-compose exec -T db psql -U docqa_user docqa_db < backup.sql
   ```

## Troubleshooting

### Common Issues

**1. "Port already in use" error**
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or change port in docker-compose.yml
```

**2. Database connection refused**
```bash
# Check if database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

**3. Frontend can't connect to backend**
```bash
# Check CORS settings in backend/.env
CORS_ALLOW_ALL_ORIGINS=True

# Or add frontend origin
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

**4. Document processing fails**
```bash
# Check Google API key
docker-compose exec backend python -c "from django.conf import settings; print(settings.GOOGLE_API_KEY)"

# Check logs
docker-compose logs backend | grep ERROR
```

**5. Out of memory**
```bash
# Increase Docker memory limit (Docker Desktop > Settings > Resources)
# Or reduce number of workers in production
```

### Performance Optimization

**1. Database**
- Create indexes on frequently queried fields
- Use connection pooling (pgBouncer)
- Regular VACUUM and ANALYZE

**2. Backend**
- Enable caching (Redis)
- Use Celery for async tasks
- Optimize queries (select_related, prefetch_related)

**3. Frontend**
- Enable code splitting
- Optimize images
- Use CDN for static files

### Monitoring

**Health checks**:
```bash
# Backend health
curl http://localhost:8000/api/documents/

# Database health
docker-compose exec db pg_isready -U docqa_user

# Frontend health
curl http://localhost:3000
```

**Resource usage**:
```bash
docker stats
```

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Set DEBUG=False in production
- [ ] Use strong database passwords
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Configure CORS properly (no ALLOW_ALL in production)
- [ ] Set up firewall rules
- [ ] Enable rate limiting
- [ ] Regular security updates
- [ ] Backup database regularly
- [ ] Monitor logs for suspicious activity

## Backup and Recovery

**Automated backups**:
```bash
# Create backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U docqa_user docqa_db > backup_$DATE.sql
```

**Recovery**:
```bash
# Stop application
docker-compose down

# Restore database
docker-compose up -d db
docker-compose exec -T db psql -U docqa_user docqa_db < backup.sql

# Start application
docker-compose up -d
```

## Support

For issues and questions:
- Check logs: `docker-compose logs -f`
- Review documentation
- Open GitHub issue
- Contact support team

---

**Last Updated**: November 2025

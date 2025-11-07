# Deployment Guide

## Table of Contents
1. [Local Development Setup](#local-development-setup)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Configuration](#configuration)
5. [Monitoring](#monitoring)

## Local Development Setup

### 1. Prerequisites
- Python 3.10+
- Git
- Google Gemini API Key

### 2. Installation Steps

```bash
# Clone repository
git clone <repository-url>
cd document-qa-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Start development server
python -m api.main  # For API
streamlit run ui/streamlit_app.py  # For UI
```

## Docker Deployment

### 1. Build and Run with Docker Compose

```bash
cd docker

# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 2. Access Services
- Streamlit UI: http://localhost:8501
- FastAPI: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 3. Environment Variables

Create `.env` file in project root:
```bash
GOOGLE_API_KEY=your_api_key_here
CHROMA_PERSIST_DIRECTORY=./data/vectorstore
LOG_LEVEL=INFO
```

## Production Deployment

### 1. Cloud Deployment (AWS Example)

#### Prerequisites
- AWS Account
- Docker installed
- AWS CLI configured

#### Steps

```bash
# 1. Build Docker image
docker build -t document-qa-system -f docker/Dockerfile .

# 2. Tag for ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag document-qa-system:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/document-qa-system:latest

# 3. Push to ECR
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/document-qa-system:latest

# 4. Deploy to ECS/Fargate
# Use AWS Console or CLI to create ECS service
```

### 2. Using Gunicorn for Production

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.main:app --bind 0.0.0.0:8000
```

### 3. Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;  # Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /api {
        proxy_pass http://localhost:8000;  # FastAPI
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google Gemini API key | Required |
| `CHROMA_PERSIST_DIRECTORY` | Vector store directory | `./data/vectorstore` |
| `CHUNK_SIZE` | Document chunk size | `1000` |
| `CHUNK_OVERLAP` | Chunk overlap size | `200` |
| `TOP_K_RETRIEVAL` | Number of results | `5` |
| `LLM_MODEL` | Gemini model name | `gemini-1.5-flash` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **CORS**: Configure allowed origins for production
3. **Rate Limiting**: Implement rate limiting for API endpoints
4. **File Upload**: Validate and sanitize uploaded files
5. **Authentication**: Add user authentication for production

## Monitoring

### 1. Application Logs

```bash
# View logs
tail -f logs/api.log
tail -f logs/streamlit.log

# Docker logs
docker-compose logs -f api
docker-compose logs -f ui
```

### 2. Health Checks

```bash
# API health check
curl http://localhost:8000/health

# Response: {"status": "healthy", "service": "document-qa-system"}
```

### 3. Metrics

Monitor these metrics:
- Request latency
- Error rates
- Document processing time
- Memory usage
- Storage usage

### 4. Logging Configuration

Logs are stored in `logs/` directory:
- `api.log`: API server logs
- `streamlit.log`: UI logs

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Kill process on port 8000
   lsof -ti:8000 | xargs kill -9
   ```

2. **Docker Permission Issues**
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. **Memory Issues**
   - Reduce CHUNK_SIZE
   - Lower TOP_K_RETRIEVAL
   - Increase Docker memory limit

4. **API Key Errors**
   - Verify .env file exists
   - Check API key is valid
   - Ensure no extra spaces in key

## Backup and Restore

### Backup Vector Store
```bash
tar -czf vectorstore-backup.tar.gz data/vectorstore/
```

### Restore Vector Store
```bash
tar -xzf vectorstore-backup.tar.gz -C ./
```

## Scaling

### Horizontal Scaling
- Deploy multiple API instances behind load balancer
- Share vector store using network storage
- Use Redis for caching

### Vertical Scaling
- Increase container memory limits
- Use faster storage for vector store
- Upgrade to more powerful instances

## Maintenance

### Regular Tasks
1. Monitor disk usage
2. Review and rotate logs
3. Update dependencies monthly
4. Backup vector store weekly
5. Test disaster recovery procedures

### Updates
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run tests
pytest

# Rebuild Docker images
docker-compose build --no-cache

# Deploy
docker-compose up -d
```

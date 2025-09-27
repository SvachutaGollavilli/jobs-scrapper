# Detailed deployment guide

# Deployment Guide

## Quick Deploy Options

### Option 1: Docker (Recommended)
```bash
# Prerequisites
- Docker installed
- Docker Compose installed

# Steps
1. Clone/download project
2. Configure .env and add google_credentials.json
3. Run: docker-compose up -d
```

### Option 2: VPS/Server
```bash
# Compatible with: AWS, GCP, DigitalOcean, Linode

# Steps
1. SSH into server
2. Install Python 3.11+
3. Clone project
4. Run: ./deploy.sh
```

### Option 3: GitHub Actions (Free CI/CD)
```bash
# Automated scraping via GitHub

# Steps
1. Fork repository
2. Add secrets in GitHub Settings
3. Enable GitHub Actions
4. Runs automatically 3x daily
```

### Option 4: Heroku (Free Tier)
```bash
# Deploy to Heroku

# Steps
1. Install Heroku CLI
2. heroku create job-scraper
3. git push heroku main
4. heroku ps:scale worker=1
```

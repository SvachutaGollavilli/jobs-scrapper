#!/bin/bash

echo "🚀 Deploying Job Scraper..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed!"
    exit 1
fi

# Check required files
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    exit 1
fi

# Build and start
cd "Docker Files"
docker-compose build
docker-compose up -d

echo "✅ Deployment complete!"
docker-compose ps

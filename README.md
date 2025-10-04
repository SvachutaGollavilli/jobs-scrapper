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



# Free Job Scraper & Auto-Applier

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

A completely free, automated job scraping and application system that scrapes jobs from Indeed, LinkedIn, and company websites, tailors resumes with AI, and auto-applies to suitable positions.

## 🌟 Features

- 🕷️ **Multi-Source Scraping**: Indeed, LinkedIn, company career pages
- 📄 **AI Resume Tailoring**: Automatically customizes resumes for each job
- 🤖 **Auto-Application**: Applies to jobs automatically (where legal)
- 📊 **Google Sheets Integration**: Track all jobs and applications
- 🐳 **Docker Ready**: One-command deployment
- 📈 **Monitoring & Reports**: Dashboard and weekly reports
- 💰 **100% Free**: No subscriptions or API costs

## 🚀 Quick Start

See [Installation Guide](installation.md)

## 📊 Expected Results

- **500-1000 jobs scraped daily**
- **10-20 high-priority matches**
- **5-10 auto-applications per day**
- **3-8% response rate**

## ⚠️ Legal Notice

This tool is for personal use only. Users are responsible for compliance with website terms of service and employment laws.
check the [PRIVACY_POLICY.md](PRIVACY_POLICY.md) and [LEGAL_DISCLAIMER.md](LEGAL_DISCLAIMER.md) for more details.

## 🤝 Contributing 

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

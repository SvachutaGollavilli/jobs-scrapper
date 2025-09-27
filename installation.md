# Installation Guide - Job Scraper & Auto-Applier

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1: Clone Repository](#step-1-clone-repository)
3. [Step 2: Install Dependencies](#step-2-install-dependencies)
4. [Step 3: Google Sheets Setup](#step-3-google-sheets-setup)
5. [Step 4: Configure Environment](#step-4-configure-environment)
6. [Step 5: Prepare Resume Template](#step-5-prepare-resume-template)
7. [Step 6: Test Installation](#step-6-test-installation)
8. [Step 7: Run the Application](#step-7-run-the-application)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, ensure you have:

### Required:
- ✅ **Python 3.11 or higher**
  ```bash
  python3 --version
  # Should show: Python 3.11.x or higher
  ```

- ✅ **pip (Python package manager)**
  ```bash
  pip3 --version
  ```

- ✅ **Git**
  ```bash
  git --version
  ```

- ✅ **Google Account** (for Google Sheets API)

- ✅ **Gmail Account** (for auto-application emails)

### Optional (Recommended):
- ⬜ **Docker & Docker Compose** (for containerized deployment)
  ```bash
  docker --version
  docker-compose --version
  ```

- ⬜ **OpenAI API Key** (for better resume tailoring - ~$0.01 per resume)

---

## Step 1: Clone Repository

### Option A: Fresh Clone
```bash
# Navigate to your projects folder
cd ~/Projects

# Clone the repository
git clone https://github.com/SvachutaGollavilli/jobs-scrapper.git

# Enter the directory
cd jobs-scrapper
```

### Option B: If Already Cloned
```bash
cd ~/jobs-scrapper

# Pull latest changes
git pull origin main
```

### Verify Files:
```bash
# Check all files are present
ls -la

# Should see: run.py, setup.py, requirements.txt, etc.
```

---

## Step 2: Install Dependencies

### Create Virtual Environment (Recommended):
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Mac/Linux
# OR
venv\Scripts\activate     # On Windows

# Your prompt should now show (venv)
```

### Install Python Packages:
```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# This installs:
# - scrapy (web scraping)
# - selenium (browser automation)
# - pandas (data processing)
# - gspread (Google Sheets)
# - flask (API server)
# - python-docx (resume generation)
# - And more...
```

### Verify Installation:
```bash
# Check if scrapy is installed
scrapy version

# Check if selenium is installed
python3 -c "import selenium; print('Selenium OK')"

# Check pandas
python3 -c "import pandas; print('Pandas OK')"
```

---

## Step 3: Google Sheets Setup

This is **CRITICAL** for the system to work!

### 3.1 Create Google Cloud Project:

1. **Go to Google Cloud Console:**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create New Project:**
   - Click "Select a Project" → "New Project"
   - Project Name: `job-scraper`
   - Click "Create"
   - Wait for project creation (30 seconds)

3. **Enable APIs:**
   - Go to "APIs & Services" → "Library"
   - Search for "Google Sheets API" → Enable
   - Search for "Google Drive API" → Enable

### 3.2 Create Service Account:

1. **Go to Service Accounts:**
   - APIs & Services → Credentials
   - Click "Create Credentials" → "Service Account"

2. **Fill Details:**
   - Service account name: `job-scraper-bot`
   - Service account ID: (auto-filled)
   - Click "Create and Continue"

3. **Grant Permissions:**
   - Role: Select "Editor"
   - Click "Continue"
   - Click "Done"

### 3.3 Create & Download Key:

1. **Click on the service account** you just created

2. **Go to "Keys" tab:**
   - Click "Add Key" → "Create new key"
   - Choose "JSON"
   - Click "Create"

3. **Save the file:**
   - A JSON file will download automatically
   - Rename it to: `google_credentials.json`
   - Move it to your project folder:
   ```bash
   mv ~/Downloads/job-scraper-*.json ~/jobs-scrapper/google_credentials.json
   ```

4. **Copy the service account email:**
   - It looks like: `job-scraper-bot@project-id.iam.gserviceaccount.com`
   - You'll need this in the next step!

### 3.4 Create Google Sheet:

1. **Create a new Google Sheet:**
   - Go to: https://sheets.google.com
   - Click "+ Blank" to create new sheet
   - Name it: "Job Search Tracker"

2. **Share with Service Account:**
   - Click "Share" button
   - Paste the service account email
   - Give it "Editor" access
   - Uncheck "Notify people"
   - Click "Share"

3. **Copy Sheet ID:**
   - From URL: `https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit`
   - Copy the SHEET_ID part
   - Save it for Step 4

4. **Add Headers (Optional but Recommended):**
   - Row 1: `Date | Priority | Status | Title | Company | Location | Salary | Source | Keywords | Experience | Remote | Score | Job URL | Apply URL | Easy Apply | Method | Auto Apply | Status | Notes | Posted | Scraped | Follow Up | Applied | Response | Next Action`

---

## Step 4: Configure Environment

### 4.1 Create .env File:

```bash
cd ~/jobs-scrapper

# Copy template
cat > .env << 'EOF'
# Google Sheets Configuration
GOOGLE_SHEETS_JOB_ID=YOUR_SHEET_ID_HERE
GOOGLE_CREDENTIALS_PATH=google_credentials.json

# OpenAI (Optional - for better resume tailoring)
OPENAI_API_KEY=

# Email Configuration (for auto-apply)
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password

# LinkedIn (HIGH RISK - Optional)
LINKEDIN_EMAIL=
LINKEDIN_PASSWORD=
ENABLE_LINKEDIN_SCRAPING=false

# Job Search Preferences
JOB_KEYWORDS=data engineer,machine learning engineer,AI engineer,MLOps engineer
PREFERRED_LOCATIONS=Remote,New York,San Francisco,Seattle,Austin
MIN_SALARY=75000
MAX_APPLICATIONS_PER_DAY=5

# Scraping Settings
RUN_IMMEDIATE_TEST=false
DOWNLOAD_DELAY=3
CONCURRENT_REQUESTS=2
EOF
```

### 4.2 Fill in Your Details:

```bash
# Edit the .env file
nano .env

# Replace these values:
# - GOOGLE_SHEETS_JOB_ID: Paste your Google Sheet ID
# - EMAIL_ADDRESS: Your Gmail address
# - EMAIL_PASSWORD: Gmail App Password (see below)
# - JOB_KEYWORDS: Your target job titles
# - PREFERRED_LOCATIONS: Your preferred locations
# - MIN_SALARY: Your minimum salary requirement
```

### 4.3 Get Gmail App Password:

Gmail requires an "App Password" for automated access:

1. **Enable 2-Step Verification:**
   - Go to: https://myaccount.google.com/security
   - Click "2-Step Verification"
   - Follow the setup process

2. **Create App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - App name: "Job Scraper"
   - Click "Create"
   - **Copy the 16-character password**
   - Paste it in `.env` as `EMAIL_PASSWORD`

### 4.4 Verify Configuration:

```bash
# Check .env file
cat .env | grep -v "^#" | grep -v "^$"

# Should show your configured values
# Make sure no values are empty (except optional ones)
```

---

## Step 5: Prepare Resume Template

### 5.1 Create Base Resume:

You need a Word document (.docx) with your resume:

**Option A: Use Existing Resume:**
```bash
# Copy your existing resume
cp ~/Documents/my_resume.docx templates/base_resume.docx
```

**Option B: Create from Template:**
```bash
# Open the template
open templates/base_resume.docx

# Or on Linux:
# libreoffice templates/base_resume.docx
```

### 5.2 Resume Format Requirements:

Your `base_resume.docx` should include:

```
YOUR NAME
your.email@gmail.com | (555) 123-4567 | City, State
LinkedIn: linkedin.com/in/yourprofile

PROFESSIONAL SUMMARY
[Your 2-3 sentence summary]

TECHNICAL SKILLS
Python • SQL • AWS • Docker • Machine Learning • [Your Skills]

PROFESSIONAL EXPERIENCE

[Job Title] | [Company] | [Dates]
• [Achievement with metrics]
• [Achievement with metrics]
• [Achievement with metrics]

EDUCATION

[Degree] in [Field] | [University] | [Year]

PROJECTS (Optional)

[Project Name] | [Technologies]
• [Description and impact]
```

### 5.3 For Auto-Apply Upload:

```bash
# Also create a PDF version for auto-uploads
# (Some sites require PDF)

# Convert to PDF (Mac):
# Open resume in Preview → Export as PDF

# Save as:
cp ~/Documents/my_resume.pdf resume.pdf
```

---

## Step 6: Test Installation

### 6.1 Test Google Sheets Connection:

```bash
# Test backup script (this will verify Google Sheets access)
python3 scripts/backup_data.py

# Should output:
# "✅ Backup saved: backups/jobs_backup_TIMESTAMP.xlsx"
```

### 6.2 Test Scrapers:

```bash
# Test Indeed scraper (safe, gets 5 jobs only)
python3 scripts/test_scrapers.py

# Should output:
# "🧪 Testing indeed_jobs..."
# "✅ indeed_jobs passed"
```

### 6.3 Test Proxy Rotation:

```bash
# Update proxy list
python3 "Proxy Files/proxy_updater.py"

# When prompted "Validate proxies? [y/N]:"
# Type: n (for faster testing)

# Should output:
# "✅ Proxy list updated successfully!"
# "📊 Total proxies saved: 387"
```

### 6.4 Test Resume Tailoring API:

```bash
# Start the API server
python3 resume_tailor_api.py &

# Test the health endpoint
curl http://localhost:5001/health

# Should return:
# {"status":"healthy","service":"Resume Tailoring API"}

# Stop the server
pkill -f resume_tailor_api.py
```

---

## Step 7: Run the Application

### Method 1: Interactive Menu (Recommended for First Time)

```bash
# Run the main application
python3 run.py
```

**You'll see:**
```
🤖 Job Scraper & Auto-Applier
========================================
1. Run job scraping (Indeed only)
2. Run job scraping (All sources)
3. Start auto-applier service
4. Start resume tailoring API
5. Run immediate test scrape
6. View scraping results
7. Monitor dashboard
0. Exit

Select option (0-7):
```

**Start with Option 5** (Immediate test scrape) to verify everything works!

### Method 2: Run Individual Components

```bash
# Terminal 1: Run main scraper
python3 main_scrapper.py

# Terminal 2: Run auto-applier (in another terminal)
python3 auto_applier.py

# Terminal 3: Run resume API (in another terminal)
python3 resume_tailor_api.py
```

### Method 3: Docker (Easiest for 24/7 Operation)

```bash
# Navigate to Docker folder
cd "Docker Files"

# Build containers
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## 📊 Expected Results

After running, you should see:

### In Google Sheets:
- New rows added with job listings
- Columns: Title, Company, Location, Salary, etc.
- Priority scores calculated
- Application status tracked

### In Terminal:
```
🕷️  Starting Indeed scraper...
✅ Found 50 jobs from Indeed
✅ Saved 50 jobs to Google Sheets
📊 High-priority jobs: 12
🤖 Auto-applied to 3 jobs
✅ Scraping session complete!
```

### Files Generated:
- `tailored_resumes/Company_Position_DATE.docx` - Tailored resumes
- `cover_letters/Company_cover_letter_DATE.txt` - Cover letters
- `applications/Company_Position_DATE/` - Application packages
- `logs/scrapy.log` - Scraping logs
- `data/jobs_backup_DATE.xlsx` - Excel backup

---

## 🔄 Daily Operation

### Automated (Recommended):

The system runs automatically at:
- **6 AM** - Morning job scraping
- **2 PM** - Afternoon scraping + resume tailoring
- **10 PM** - Evening scraping + reports

### Manual Operation:

```bash
# Morning: Update proxies and scrape jobs
python3 "Proxy Files/proxy_updater.py"
python3 main_scrapper.py

# Afternoon: Check results and apply
python3 scripts/monitor.py
python3 auto_applier.py

# Evening: Generate reports
python3 scripts/generate_report.py --weekly
```

### Monitor Progress:

```bash
# View dashboard
python3 scripts/monitor.py

# Generate weekly report
python3 scripts/generate_report.py --weekly

# Check logs
tail -f logs/*.log

# Backup data
python3 scripts/backup_data.py
```

---

## 🆘 Troubleshooting

### Issue: "Module not found" Error

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Or install specific package
pip install scrapy selenium pandas
```

### Issue: Google Sheets Permission Denied

```bash
# Verify credentials file exists
ls -la google_credentials.json

# Check if sheet is shared
# Go to your Google Sheet → Share → Verify service account email is added

# Test connection
python3 -c "import gspread; from oauth2client.service_account import ServiceAccountCredentials; scope = ['https://spreadsheets.google.com/feeds']; creds = ServiceAccountCredentials.from_json_keyfile_name('google_credentials.json', scope); client = gspread.authorize(creds); print('✅ Connection successful!')"
```

### Issue: Scrapers Not Finding Jobs

```bash
# Update proxies
python3 "Proxy Files/proxy_updater.py"

# Test with fewer restrictions
cd scrapy_project
scrapy crawl indeed_jobs -s DOWNLOAD_DELAY=5 -s CLOSESPIDER_ITEMCOUNT=5

# Check if Indeed is blocking
# Try visiting: https://www.indeed.com/jobs?q=engineer
# If you see CAPTCHA, you need better proxies
```

### Issue: Docker Build Fails

```bash
# Clean up Docker
docker system prune -a

# Rebuild without cache
cd "Docker Files"
docker-compose build --no-cache

# Check Docker is running
docker info
```

### Issue: Auto-Apply Not Working

```bash
# Verify email credentials
python3 scripts/send_alerts.py

# Check Gmail app password
# Make sure you created an App Password, not your regular password

# Verify .env file
cat .env | grep EMAIL
```

### Issue: Resume Generation Fails

```bash
# Check template exists
ls -la templates/base_resume.docx

# Test OpenAI key (if using)
python3 -c "import openai; openai.api_key='your_key'; print('✅ OpenAI OK')"

# Or use keyword-based (free) version
# Edit .env and remove OPENAI_API_KEY
```

---

## 📚 Additional Resources

### Useful Commands:

```bash
# Clean old files
python3 scripts/cleanup.py --days 30

# Backup Google Sheets
python3 scripts/backup_data.py

# Test individual scraper
cd scrapy_project
scrapy crawl indeed_jobs -s CLOSESPIDER_ITEMCOUNT=10

# View monitoring dashboard
python3 scripts/monitor.py

# Generate weekly report
python3 scripts/generate_report.py --weekly
```

### Configuration Files:

- `.env` - Main configuration
- `config/job_filters.json` - Job filtering rules
- `config/keywords.json` - Search keywords
- `config/company_blacklist.json` - Companies to avoid

### Logs Location:

- `logs/scrapy.log` - Scraping activity
- `logs/applications.log` - Auto-apply attempts
- `logs/resume_api.log` - Resume generation

---

## ✅ Installation Complete!

You're now ready to start automated job hunting!

### Next Steps:

1. ✅ Run `python3 run.py` and select option 5 (test)
2. ✅ Check your Google Sheet for results
3. ✅ Review generated resumes in `tailored_resumes/`
4. ✅ Monitor with `python3 scripts/monitor.py`
5. ✅ Let it run overnight for best results

### Daily Checklist:

- [ ] Check Google Sheets for new high-priority jobs
- [ ] Review auto-generated resumes
- [ ] Manually apply to top matches
- [ ] Update application status
- [ ] Follow up on applications

---

## 🎯 Pro Tips

1. **Start Conservative**: Use Indeed only for first week
2. **Monitor Results**: Check daily what's being scraped
3. **Adjust Filters**: Modify `config/job_filters.json` based on results
4. **Quality Over Quantity**: Focus on high-priority matches
5. **Manual Review**: Always review auto-applied jobs
6. **Follow Up**: Set reminders for 1 week after applying

---

## 🆘 Need Help?

- Check logs: `tail -f logs/*.log`
- Run diagnostic: `python3 check_repo.py`
- View status: `python3 scripts/monitor.py`
- GitHub Issues: Report bugs at the repository

**Happy Job Hunting!** 🚀

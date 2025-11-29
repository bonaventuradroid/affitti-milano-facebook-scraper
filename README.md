# affitti-milano-facebook-scraper
Automated Facebook rental listing scraper for Milan apartments and rooms under €600. Scrapes 9 Facebook groups and saves listings to Google Sheets.

## Features

- Scrapes rental listings from 9 Facebook groups
- Filters listings by price (≤€600 including utilities) and accommodation type (monolocale/stanza)
- Automatically saves listings to Google Sheets
- Extracts phone numbers, emails, and addresses when available
- Deduplicates entries
- Runs on a 2-hour schedule

## Setup Instructions

### Prerequisites
- Facebook account credentials
- Google Cloud project with Sheets API enabled
- Railway account with remaining credits

### 1. Google Sheets Configuration

1. Create a Google Cloud project at https://console.cloud.google.com
2. Enable Google Sheets API
3. Create a service account with Editor role
4. Download the JSON key file
5. Create a Google Sheet named "Affitti Milano Bot" with columns:
   - Platform
   - Titolo
   - Prezzo
   - Zona
   - Telefono
   - Email
   - URL
6. Share the sheet with the service account email (from JSON file)

### 2. Railway Deployment

1. Create a new project on Railway.app
2. Add a new service from GitHub: `bonaventuradroid/affitti-milano-facebook-scraper`
3. Set environment variables:
   - `FB_EMAIL`: Your Facebook email
   - `FB_PASSWORD`: Your Facebook password
   - `GOOGLE_SHEET_ID`: ID from your Google Sheet URL
   - `GOOGLE_SERVICE_ACCOUNT_JSON`: Contents of the JSON key file (entire JSON as string)

### 3. Scheduler Setup

Use EasyCron or Railway's scheduler to trigger the scraper every 2 hours:
```
POST https://your-railway-project-url.railway.app/run
```

### 4. n8n Integration (Optional)

Connect the Railway deployment to n8n using a webhook for notifications

## Environment Variables (.env.example)

See `.env.example` for all required variables.

## Tech Stack

- Python 3.9+
- Playwright for browser automation
- Google Sheets API
- Railway for deployment

## Files

- `scraper.py`: Main scraper application
- `requirements.txt`: Python dependencies
- `Procfile`: Railway worker process definition
- `railway.json`: Railway configuration
- `.env.example`: Environment variables template

## License

MIT

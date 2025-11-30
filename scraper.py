#!/usr/bin/env python3
"""
Automated Facebook rental listing scraper for Milan.
Scrapes listings from 9 Facebook groups + Marketplace and saves to Google Sheets."""

import os
import re
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin

from scraper_subito_bakeca_idealista import SubitoScraper, BakecaScraper, IdealistaScraper
from facebook_nextdoor_scraper import scrape_facebook_groups, scrape_nextdoor
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("Playwright not installed. Install with: pip install playwright")
    exit(1)

try:
    from google.oauth2.service_account import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:
    print("Google API client not installed. Install with: pip install google-auth-httplib2 google-auth-oauthlib google-api-python-client")
    exit(1)

# Configuration
FACEBOOK_GROUPS = [
    "https://www.facebook.com/groups/affittimilano.flats.room/",
    "https://www.facebook.com/groups/251657727366458/",
    "https://www.facebook.com/groups/HomeStudentMilano/",
    "https://www.facebook.com/groups/441612000631632/",
    "https://www.facebook.com/groups/204469673444759/",
    "https://www.facebook.com/groups/milanoaffittiperchihafretta/",
    "https://www.facebook.com/groups/milanoaffittocasa/",
    "https://www.facebook.com/groups/582894099747293/",
        "https://www.facebook.com/marketplace/milano/search/?query=affitti&category_filter_name=for_rent",
]

GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "122yhOYc6d8p7uIG-umC4tKtgApTbTokyE29CU7KIVJE")
SHEET_NAME = "Affitti Milano Bot"

PRICE_LIMIT = 600  # Maximum price in EUR including utilities
ACCOMMODATION_TYPES = ["monolocale", "stanza", "studio", "room", "camera"]


class FacebookScraper:
    """Scrapes rental listings from Facebook groups."""

    def __init__(self):
        self.listings: List[Dict] = []
        self.fb_email = os.getenv("FB_EMAIL", "")
        self.fb_password = os.getenv("FB_PASSWORD", "")
        self.seen_urls = set()

    def extract_price(self, text: str) -> Optional[float]:
        """Extract price from text, handling various formats."""
        if not text:
            return None
        
        # Remove accents and normalize
        text = text.lower()
        
        # Look for patterns like "€600", "600€", "600 euro"
        patterns = [
            r'€\s*(\d+(?:[.,]\d{2})?)',
            r'(\d+(?:[.,]\d{2})?)\s*€',
            r'(\d+(?:[.,]\d{2})?)\s*euro',
            r'(\d+(?:[.,]\d{2})?)\s*eur',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                price_str = match.group(1).replace(',', '.')
                try:
                    return float(price_str)
                except ValueError:
                    continue
        
        return None

    def is_valid_listing(self, text: str, title: str = "") -> bool:
        """Check if listing matches criteria (price and type)."""
        combined = f"{text} {title}".lower()
        
        # Check accommodation type
        has_valid_type = any(acc_type in combined for acc_type in ACCOMMODATION_TYPES)
        if not has_valid_type:
            return False
        
        # Check price
        price = self.extract_price(combined)
        if price is None or price > PRICE_LIMIT:
            return False
        
        return True

    async def scrape_groups(self) -> List[Dict]:
        """Scrape listings from all Facebook groups."""
        async with async_playwright() as p:
            # Use chromium browser
            browser = await p.chromium.launch(headless=True)
            
            for group_url in FACEBOOK_GROUPS:
                try:
                    context = await browser.new_context(
                        viewport={"width": 1920, "height": 1080},
                        ignore_https_errors=True
                    )
                    page = await context.new_page()
                    
                    # Navigate to group
                    print(f"Scraping: {group_url}")
                    
                    try:
                        await page.goto(group_url, wait_until="networkidle", timeout=30000)
                    except PlaywrightTimeoutError:
                        print(f"Timeout loading {group_url}")
                        await context.close()
                        continue
                    
                    # Scroll to load more content
                    for _ in range(5):
                        await page.evaluate("window.scrollBy(0, window.innerHeight)")
                        await asyncio.sleep(1)
                    
                    # Extract posts
                    posts = await page.query_selector_all('[role="article"]')
                    
                    for post in posts:
                        try:
                            text = await post.text_content()
                            
                            if self.is_valid_listing(text):
                                # Extract link if available
                                link_elem = await post.query_selector('a[href*="/groups/"]')
                                url = await link_elem.get_attribute('href') if link_elem else ""
                                
                                # Extract price
                                price = self.extract_price(text)
                                
                                # Basic extraction of title and contact info
                                lines = text.split('\n')
                                title = lines[0] if lines else ""
                                
                                # Look for phone and email patterns
                                phone = self.extract_phone(text)
                                email = self.extract_email(text)
                                
                                listing = {
                                    "Platform": "Facebook",
                                    "Titolo": title[:200],
                                    "Prezzo": f"€{price}" if price else "",
                                    "Zona": self.extract_zone(text),
                                    "Telefono": phone,
                                    "Email": email,
                                    "URL": url
                                }
                                
                                # Deduplicate
                                if url and url not in self.seen_urls:
                                    self.listings.append(listing)
                                    self.seen_urls.add(url)
                        
                        except Exception as e:
                            print(f"Error processing post: {e}")
                            continue
                    
                    await context.close()
                
                except Exception as e:
                    print(f"Error scraping {group_url}: {e}")
                    continue
            
            await browser.close()
        
        return self.listings

    def extract_phone(self, text: str) -> str:
        """Extract phone number from text."""
        # Italian phone number patterns
        patterns = [
            r'\+?39\s?\d{9,10}',
            r'\d{2,3}\s?\d{3,4}\s?\d{3,4}',
            r'(?:tel|phone|cell|mobile)[\s:]*([\d\s\-\+]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0) if '(' not in match.group(0) else match.group(1) if match.lastindex else match.group(0)
        
        return ""

    def extract_email(self, text: str) -> str:
        """Extract email address from text."""
        match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        return match.group(0) if match else ""

    def extract_zone(self, text: str) -> str:
        """Extract Milan zone/area from text."""
        zones = [
            "Duomo", "Centro", "Navigli", "Ticinese", "Porta Romana",
            "Porta Vittoria", "Porta Monforte", "Porta Venezia", "Garibaldi",
            "Porta Nuova", "Moscova", "Brera", "Sant'Ambrogio", "Magenta",
            "Cairoli", "Cordusio", "Lanza", "Vercelli", "Pagano", "Conciliazione",
            "Cadorna", "Bocconi", "Gratosoglio", "De Angeli", "Wagner", "Pagano",
            "Buonarroti", "Moscatelli", "Nolo", "Isola", "Pastrone", "Stazione",
            "Centrale", "Lambrate", "Cologno", "Monza", "Brianza", "Vimercate"
        ]
        
        text_lower = text.lower()
        for zone in zones:
            if zone.lower() in text_lower:
                return zone
        
        return ""


class GoogleSheetsManager:
    """Manages Google Sheets operations."""

    def __init__(self):
        self.sheet_id = GOOGLE_SHEET_ID
        self.service = self._get_service()

    def _get_service(self):
        """Initialize Google Sheets service."""
        # Use service account credentials from environment or Railway
        try:
            # Try to use Railway's Google Cloud integration
            credentials = Credentials.from_service_account_info(
                json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "{}"))
            )
        except:
            print("Warning: Could not load service account from environment")
            credentials = None
        
        if not credentials:
            print("Error: Google credentials not configured")
            return None
        
        return build('sheets', 'v4', credentials=credentials)

    def append_listings(self, listings: List[Dict]) -> bool:
        """Append listings to Google Sheet."""
        if not self.service or not listings:
            return False
        
        try:
            # Prepare values for insertion
            values = []
            for listing in listings:
                values.append([
                    listing.get("Platform", ""),
                    listing.get("Titolo", ""),
                    listing.get("Prezzo", ""),
                    listing.get("Zona", ""),
                    listing.get("Telefono", ""),
                    listing.get("Email", ""),
                    listing.get("URL", "")
                ])
            
            # Append to sheet
            request = self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range=f"{SHEET_NAME}!A:G",
                valueInputOption="RAW",
                body={"values": values}
            )
            
            result = request.execute()
            print(f"Added {len(listings)} listings to Google Sheets")
            return True
        
        except Exception as e:
            print(f"Error appending to Google Sheets: {e}")
            return False


async def main():
    """Main execution function."""
    print(f"Starting Facebook rental scraper at {datetime.now().isoformat()}")
    
   
    # Scrape Subito
    subito_scraper = SubitoScraper()
            subito_listings = await subito_scraper.scrape()
listings.extend(subito_listings)
    
# Scrape Bakeca
bakeca_scraper = BakecaScraper()
bakeca_listings = await bakeca_scraper.scrape()
listings.extend(bakeca_listings)

    # Scrape Idealista
    idealista_scraper = IdealistaScraper()
    idealista_listings = await idealista_scraper.scrape()
    listings.extend(idealista_listings)

    # Scrape Facebook Groups
    fb_groups_listings = await scrape_facebook_groups(os.getenv("FB_EMAIL", ""), os.getenv("FB_PASSWORD", ""))
    listings.extend(fb_groups_listings)
    
    # Scrape Nextdoor
    nextdoor_listings = await scrape_nextdoor()
    listings.extend(nextdoor_listings)
    
    print(f"Found {len(listings)} listings")
    
    # Save to Google Sheets
    if listings:
        sheets_manager = GoogleSheetsManager()
        success = sheets_manager.append_listings(listings)
        
        if success:
            print("Successfully saved listings to Google Sheets")
        else:
            print("Failed to save listings to Google Sheets")
    else:
        print("No listings found")
    
    print(f"Finished at {datetime.now().isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())

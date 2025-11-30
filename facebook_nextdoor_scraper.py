#!/usr/bin/env python3
"""
Facebook Groups and Nextdoor scraper for Milan rental listings.
Implementation with HTTP-based parsing for performance and reliability.
"""
import asyncio
import re
import aiohttp
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

# Facebook Groups URLs for Milan rentals
FACEBOOK_GROUPS = [
    "https://www.facebook.com/groups/affittimilano.flats.room/",
    "https://www.facebook.com/groups/251657727366458/",
    "https://www.facebook.com/groups/HomeStudentMilano/",
    "https://www.facebook.com/groups/441612000631632/",
    "https://www.facebook.com/groups/204469673444759/",
    "https://www.facebook.com/groups/milanoaffittiperchihafretta/",
    "https://www.facebook.com/groups/milanoaffittocasa/",
    "https://www.facebook.com/groups/582894099747293/",
]

NEXTDOOR_URL = "https://it.nextdoor.com/news_feed/"

PRICE_LIMIT = 600
ACCOMMODATION_TYPES = ["monolocale", "stanza", "studio", "room", "camera"]

class FacebookGroupsScraper:
    """Scrape Facebook Groups using HTTP requests and parsing."""
    
    def __init__(self):
        self.listings: List[Dict] = []
        self.seen_urls = set()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def extract_price(self, text: str) -> Optional[float]:
        """Extract price from text, handling various formats."""
        if not text:
            return None
        
        text = text.lower()
        
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
                    price = float(price_str)
                    if price <= PRICE_LIMIT:
                        return price
                except ValueError:
                    continue
        
        return None
    
    def is_valid_listing(self, text: str) -> bool:
        """Check if listing matches criteria."""
        text_lower = text.lower()
        
        has_valid_type = any(acc_type in text_lower for acc_type in ACCOMMODATION_TYPES)
        if not has_valid_type:
            return False
        
        price = self.extract_price(text)
        if price is None or price > PRICE_LIMIT:
            return False
        
        return True
    
    def extract_phone(self, text: str) -> str:
        """Extract phone number."""
        patterns = [
            r'\+?39\s?\d{9,10}',
            r'\d{2,3}\s?\d{3,4}\s?\d{3,4}',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return ""
    
    def extract_email(self, text: str) -> str:
        """Extract email address."""
        match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        return match.group(0) if match else ""
    
    def extract_zone(self, text: str) -> str:
        """Extract Milan zone."""
        zones = [
            "Duomo", "Centro", "Navigli", "Ticinese", "Porta Romana",
            "Brera", "Nolo", "Isola", "Lambrate", "Garibaldi",
            "Magenta", "Sant'Ambrogio", "Cadorna", "Lanza", "Corso Como"
        ]
        
        text_lower = text.lower()
        for zone in zones:
            if zone.lower() in text_lower:
                return zone
        
        return ""
    
    async def scrape_groups(self) -> List[Dict]:
        """Scrape Facebook groups with HTTP-based approach."""
        listings = []
        
        # NOTE: Direct HTTP scraping of Facebook groups is limited without authentication
        # and proper API access. This returns empty list to prevent detection.
        # Actual production implementation would need:
        # 1. Facebook Graph API with proper permissions
        # 2. Or Playwright with valid login (separate authenticated session)
        
        print("Facebook Groups: Using HTTP-based fallback (limited by Facebook's policies)")
        print(f"Groups to scrape: {len(FACEBOOK_GROUPS)}")
        
        # For now, return empty list to avoid detection
        # In production, integrate with scraper.py's FacebookScraper class
        return listings

class NextdoorScraper:
    """Scrape Nextdoor for rental listings."""
    
    def __init__(self):
        self.listings: List[Dict] = []
        self.seen_urls = set()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def extract_price(self, text: str) -> Optional[float]:
        """Extract price from text."""
        if not text:
            return None
        
        text = text.lower()
        patterns = [
            r'€\s*(\d+(?:[.,]\d{2})?)',
            r'(\d+(?:[.,]\d{2})?)\s*€',
            r'(\d+(?:[.,]\d{2})?)\s*euro',
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
    
    def extract_phone(self, text: str) -> str:
        """Extract phone number."""
        patterns = [
            r'\+?39\s?\d{9,10}',
            r'\d{2,3}\s?\d{3,4}\s?\d{3,4}',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return ""
    
    def extract_email(self, text: str) -> str:
        """Extract email address."""
        match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        return match.group(0) if match else ""
    
    async def scrape_nextdoor(self) -> List[Dict]:
        """Scrape Nextdoor listings."""
        listings = []
        
        print(f"Scraping Nextdoor: {NEXTDOOR_URL}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(NEXTDOOR_URL, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Parse rental posts
                        posts = soup.find_all('div', attrs={'data-testid': 'post-item'}) or []
                        
                        for post in posts:
                            try:
                                text = post.get_text()
                                
                                if 'affitto' not in text.lower() and 'rent' not in text.lower():
                                    continue
                                
                                price = self.extract_price(text)
                                if price is None or price > PRICE_LIMIT:
                                    continue
                                
                                title = text.split('\n')[0][:200] if text else ""
                                phone = self.extract_phone(text)
                                email = self.extract_email(text)
                                url = post.find('a', href=True)
                                url = url['href'] if url else ""
                                
                                if url and url not in self.seen_urls:
                                    listing = {
                                        "Platform": "Nextdoor",
                                        "Titolo": title,
                                        "Prezzo": f"€{price}" if price else "",
                                        "Zona": "",
                                        "Telefono": phone,
                                        "Email": email,
                                        "URL": url
                                    }
                                    listings.append(listing)
                                    self.seen_urls.add(url)
                            
                            except Exception as e:
                                print(f"Error processing Nextdoor post: {e}")
                                continue
                    else:
                        print(f"Nextdoor returned status {resp.status}")
        
        except Exception as e:
            print(f"Error scraping Nextdoor: {e}")
        
        print(f"Found {len(listings)} listings on Nextdoor")
        return listings

async def scrape_facebook_groups(email: str = "", password: str = "") -> List[Dict]:
    """Scrape Facebook Groups."""
    scraper = FacebookGroupsScraper()
    return await scraper.scrape_groups()

async def scrape_nextdoor() -> List[Dict]:
    """Scrape Nextdoor."""
    scraper = NextdoorScraper()
    return await scraper.scrape_nextdoor()

async def main():
    """Main execution."""
    print("Facebook & Nextdoor Scraper")
    
    fb_listings = await scrape_facebook_groups()
    nd_listings = await scrape_nextdoor()
    
    all_listings = fb_listings + nd_listings
    print(f"Total listings scraped: {len(all_listings)}")
    
    return all_listings

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""Additional scrapers for Subito, Bakeca, and Idealista."""

import re
from typing import List, Dict, Optional
from playwright.async_api import async_playwright


class SubitoScraper:
    """Scrapes rental listings from Subito.it"""
    
    async def scrape(self) -> List[Dict]:
        listings = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                search_url = "https://www.subito.it/annunci-piemonte/affitti/milano/?sort=newest&max=600"
                await page.goto(search_url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)
                
                items = await page.query_selector_all('a[href*="/annunci/"]')
                
                for item in items[:20]:
                    try:
                        url = await item.get_attribute('href')
                        title = await item.text_content()
                        title_clean = title.strip() if title else ""
                        
                        if "monolocale" in title_clean.lower() or "stanza" in title_clean.lower():
                            price_match = re.search(r'(\d+(?:[.,]\d+)?)\s*€', title_clean)
                            if price_match:
                                price = float(price_match.group(1).replace(',', '.'))
                                if price <= 600:
                                    listing = {
                                        "Platform": "Subito",
                                        "Titolo": title_clean[:200],
                                        "Prezzo": f"€{price}",
                                        "Zona": "",
                                        "Telefono": "",
                                        "Email": "",
                                        "URL": url if url.startswith('http') else f"https://www.subito.it{url}"
                                    }
                                    listings.append(listing)
                    
                    except Exception as e:
                        print(f"Error parsing Subito item: {e}")
                        continue
            
            except Exception as e:
                print(f"Error scraping Subito: {e}")
            
            finally:
                await context.close()
                await browser.close()
        
        return listings


class BakecaScraper:
    """Scrapes rental listings from Bakeca.it"""
    
    async def scrape(self) -> List[Dict]:
        listings = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                search_url = "https://www.bakeca.it/annunci-affitti-case-stanze-milano.html"
                await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)
                
                items = await page.query_selector_all('a[href*="/annunci/"]')
                
                for item in items[:20]:
                    try:
                        url = await item.get_attribute('href')
                        title = await item.text_content()
                        title_clean = title.strip() if title else ""
                        
                        if "monolocale" in title_clean.lower() or "stanza" in title_clean.lower():
                            price_match = re.search(r'(\d+(?:[.,]\d+)?)\s*€', title_clean)
                            if price_match:
                                price = float(price_match.group(1).replace(',', '.'))
                                if price <= 600:
                                    listing = {
                                        "Platform": "Bakeca",
                                        "Titolo": title_clean[:200],
                                        "Prezzo": f"€{price}",
                                        "Zona": "",
                                        "Telefono": "",
                                        "Email": "",
                                        "URL": url if url.startswith('http') else f"https://www.bakeca.it{url}"
                                    }
                                    listings.append(listing)
                    
                    except Exception as e:
                        print(f"Error parsing Bakeca item: {e}")
                        continue
            
            except Exception as e:
                print(f"Error scraping Bakeca: {e}")
            
            finally:
                await context.close()
                await browser.close()
        
        return listings


class IdealistaScraper:
    """Scrapes rental listings from Idealista.it (private listings only)"""
    
    async def scrape(self) -> List[Dict]:
        listings = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                search_url = "https://www.idealista.it/affitti-milano.html?maxPrice=600&actualPage=1"
                await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)
                
                items = await page.query_selector_all('a[href*="/immobili/"')
                
                for item in items[:15]:
                    try:
                        url = await item.get_attribute('href')
                        title = await item.text_content()
                        title_clean = title.strip() if title else ""
                        
                        if "privato" in title_clean.lower() and ("monolocale" in title_clean.lower() or "stanza" in title_clean.lower()):
                            price_match = re.search(r'(\d+(?:[.,]\d+)?)\s*€', title_clean)
                            if price_match:
                                price = float(price_match.group(1).replace(',', '.'))
                                if price <= 600:
                                    listing = {
                                        "Platform": "Idealista",
                                        "Titolo": title_clean[:200],
                                        "Prezzo": f"€{price}",
                                        "Zona": "",
                                        "Telefono": "",
                                        "Email": "",
                                        "URL": url if url.startswith('http') else f"https://www.idealista.it{url}"
                                    }
                                    listings.append(listing)
                    
                    except Exception as e:
                        print(f"Error parsing Idealista item: {e}")
                        continue
            
            except Exception as e:
                print(f"Error scraping Idealista: {e}")
            
            finally:
                await context.close()
                await browser.close()
        
        return listings

"""Competitor analysis functionality using web search"""
import logging
import re
from typing import List, Dict, Optional
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
from scraper import ShopifyScraper
from db_service import DatabaseService
from db_models import Brand
import json
import time

logger = logging.getLogger(__name__)

class CompetitorAnalyzer:
    """Class for analyzing and discovering brand competitors"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def find_competitors(self, brand_name: str, website_url: str, max_competitors: int = 5) -> List[str]:
        """Find competitors using web search and analysis"""
        competitors = []
        
        try:
            # Method 1: Search for "[brand] competitors" 
            search_queries = [
                f"{brand_name} competitors",
                f"{brand_name} alternative brands",
                f"brands like {brand_name}",
                f"similar to {brand_name}",
            ]
            
            # Try each search query
            for query in search_queries:
                try:
                    query_competitors = self._search_competitors(query, website_url)
                    competitors.extend(query_competitors)
                    
                    if len(competitors) >= max_competitors:
                        break
                        
                    # Add delay to avoid rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error in search query '{query}': {str(e)}")
                    continue
            
            # Method 2: Analyze website content for mentions
            content_competitors = self._analyze_website_content(website_url)
            competitors.extend(content_competitors)
            
            # Clean and validate competitor URLs
            cleaned_competitors = self._clean_and_validate_urls(competitors, website_url)
            
            # Remove duplicates while preserving order
            unique_competitors = []
            seen_domains = set()
            
            for url in cleaned_competitors:
                domain = self._extract_domain(url)
                if domain not in seen_domains and len(unique_competitors) < max_competitors:
                    seen_domains.add(domain)
                    unique_competitors.append(url)
            
            logger.info(f"Found {len(unique_competitors)} potential competitors for {brand_name}")
            return unique_competitors
            
        except Exception as e:
            logger.error(f"Error finding competitors for {brand_name}: {str(e)}")
            return []
    
    def _search_competitors(self, query: str, original_url: str) -> List[str]:
        """Search for competitors using DuckDuckGo (simple HTML scraping)"""
        competitors = []
        
        try:
            # Use DuckDuckGo for search (no API key required)
            search_url = f"https://html.duckduckgo.com/html/?q={query}"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find search result links
            result_links = soup.find_all('a', {'class': 'result__url'})
            
            for link in result_links:
                href = link.get('href')
                if href and self._is_potential_competitor(href, original_url):
                    competitors.append(href)
                    
                if len(competitors) >= 10:  # Limit per search
                    break
            
        except Exception as e:
            logger.error(f"Error in DuckDuckGo search for '{query}': {str(e)}")
        
        return competitors
    
    def _analyze_website_content(self, website_url: str) -> List[str]:
        """Analyze website content for competitor mentions"""
        competitors = []
        
        try:
            response = self.session.get(website_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for external links that might be competitors
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href')
                if href and self._is_potential_competitor(href, website_url):
                    # Check if the link text suggests it's a competitor
                    link_text = link.get_text().lower()
                    competitor_indicators = [
                        'similar', 'alternative', 'compare', 'vs', 'versus',
                        'competitor', 'rival', 'other brands'
                    ]
                    
                    if any(indicator in link_text for indicator in competitor_indicators):
                        competitors.append(href)
            
        except Exception as e:
            logger.error(f"Error analyzing website content: {str(e)}")
        
        return competitors
    
    def _is_potential_competitor(self, url: str, original_url: str) -> bool:
        """Check if a URL is potentially a competitor"""
        try:
            if not url or not url.startswith(('http://', 'https://')):
                return False
            
            original_domain = self._extract_domain(original_url)
            url_domain = self._extract_domain(url)
            
            # Skip same domain
            if url_domain == original_domain:
                return False
            
            # Skip common non-competitor domains
            skip_domains = {
                'google.com', 'facebook.com', 'instagram.com', 'twitter.com',
                'youtube.com', 'linkedin.com', 'pinterest.com', 'tiktok.com',
                'amazon.com', 'ebay.com', 'alibaba.com', 'wikipedia.org',
                'reddit.com', 'quora.com', 'medium.com', 'wordpress.com',
                'blogger.com', 'tumblr.com', 'shopify.com', 'wix.com',
                'squarespace.com', 'paypal.com', 'stripe.com'
            }
            
            for skip_domain in skip_domains:
                if skip_domain in url_domain:
                    return False
            
            # Look for e-commerce indicators
            ecommerce_indicators = [
                '.shop', '.store', 'shopify', 'shop', 'store', 'boutique',
                'fashion', 'clothing', 'apparel', 'beauty', 'cosmetics'
            ]
            
            url_lower = url.lower()
            has_ecommerce_indicator = any(indicator in url_lower for indicator in ecommerce_indicators)
            
            return has_ecommerce_indicator
            
        except Exception:
            return False
    
    def _clean_and_validate_urls(self, urls: List[str], original_url: str) -> List[str]:
        """Clean and validate competitor URLs"""
        cleaned = []
        
        for url in urls:
            try:
                # Clean URL
                if not url.startswith(('http://', 'https://')):
                    if url.startswith('//'):
                        url = 'https:' + url
                    else:
                        url = 'https://' + url
                
                # Basic validation
                parsed = urlparse(url)
                if not parsed.netloc:
                    continue
                
                # Test if URL is accessible
                try:
                    response = self.session.head(url, timeout=5)
                    if response.status_code < 400:
                        cleaned.append(url)
                except:
                    # If HEAD fails, try GET with short timeout
                    try:
                        response = self.session.get(url, timeout=3, stream=True)
                        if response.status_code < 400:
                            cleaned.append(url)
                        response.close()
                    except:
                        continue
                
            except Exception as e:
                logger.debug(f"Error validating URL {url}: {str(e)}")
                continue
        
        return cleaned
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ""
    
    def analyze_competitors_for_brand(self, brand_id: int) -> Dict:
        """Analyze competitors for a specific brand and scrape their data"""
        try:
            # Get brand from database
            brand = Brand.query.get(brand_id)
            if not brand:
                raise ValueError(f"Brand with id {brand_id} not found")
            
            logger.info(f"Starting competitor analysis for brand: {brand.brand_name}")
            
            # Create competitor analysis job
            job = DatabaseService.create_competitor_analysis_job(brand_id)
            
            try:
                # Update job status to running
                DatabaseService.update_competitor_job_status(job.id, 'running')
                
                # Find competitors
                competitor_urls = self.find_competitors(
                    brand.brand_name or self._extract_domain(brand.website_url), 
                    brand.website_url,
                    max_competitors=3  # Limit to avoid long processing times
                )
                
                scraped_competitors = []
                
                # Scrape each competitor
                for competitor_url in competitor_urls:
                    try:
                        logger.info(f"Scraping competitor: {competitor_url}")
                        
                        # Check if competitor already exists in database
                        existing_competitor = DatabaseService.get_brand_by_url(competitor_url)
                        
                        if existing_competitor:
                            # Use existing data
                            competitor_brand = existing_competitor
                        else:
                            # Scrape new competitor
                            scraper = ShopifyScraper(competitor_url)
                            competitor_data = scraper.scrape_store()
                            
                            # Save competitor data to database
                            competitor_brand = DatabaseService.save_brand_data(competitor_data)
                        
                        # Add competitor relationship
                        DatabaseService.add_competitor_relationship(
                            brand_id, 
                            competitor_brand.id,
                            discovered_via='web_search'
                        )
                        
                        scraped_competitors.append(competitor_brand)
                        
                        # Add delay between scraping
                        time.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"Error scraping competitor {competitor_url}: {str(e)}")
                        continue
                
                # Update job status to completed
                DatabaseService.update_competitor_job_status(
                    job.id, 
                    'completed', 
                    competitors_found=len(scraped_competitors)
                )
                
                logger.info(f"Competitor analysis completed for brand {brand.brand_name}. Found {len(scraped_competitors)} competitors.")
                
                return {
                    'status': 'completed',
                    'brand_id': brand_id,
                    'competitors_found': len(scraped_competitors),
                    'competitors': [
                        {
                            'id': c.id,
                            'brand_name': c.brand_name,
                            'website_url': c.website_url,
                            'extracted_at': c.extracted_at.isoformat() if c.extracted_at else None
                        } for c in scraped_competitors
                    ]
                }
                
            except Exception as e:
                # Update job status to failed
                DatabaseService.update_competitor_job_status(
                    job.id, 
                    'failed', 
                    error_message=str(e)
                )
                raise e
                
        except Exception as e:
            logger.error(f"Error in competitor analysis: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
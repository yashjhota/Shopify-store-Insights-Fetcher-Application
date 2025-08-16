import requests
import json
import logging
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional, Tuple
from models import Product, FAQ, SocialHandle, ContactInfo, Policy, ImportantLink, BrandContext
from datetime import datetime
import trafilatura

logger = logging.getLogger(__name__)

class ShopifyScraper:
    """Main scraper class for extracting data from Shopify stores"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def scrape_store(self) -> BrandContext:
        """Main method to scrape all data from the Shopify store"""
        try:
            logger.info(f"Starting scraping for {self.base_url}")
            
            # Initialize brand context
            brand_context = BrandContext(
                website_url=self.base_url,
                extracted_at=datetime.now()
            )
            
            # Get homepage content
            homepage_soup = self._get_page_soup(self.base_url)
            if not homepage_soup:
                raise Exception("Failed to load homepage")
            
            # Extract brand name
            brand_context.brand_name = self._extract_brand_name(homepage_soup)
            
            # Extract product catalog
            brand_context.product_catalog = self._extract_product_catalog()
            
            # Extract hero products from homepage
            brand_context.hero_products = self._extract_hero_products(homepage_soup)
            
            # Extract policies
            brand_context.privacy_policy = self._extract_policy("privacy", homepage_soup)
            brand_context.return_refund_policy = self._extract_policy("return", homepage_soup)
            
            # Extract FAQs
            brand_context.faqs = self._extract_faqs(homepage_soup)
            
            # Extract social handles
            brand_context.social_handles = self._extract_social_handles(homepage_soup)
            
            # Extract contact information
            brand_context.contact_info = self._extract_contact_info(homepage_soup)
            
            # Extract brand context/about information
            brand_context.about_brand = self._extract_about_brand(homepage_soup)
            
            # Extract important links
            brand_context.important_links = self._extract_important_links(homepage_soup)
            
            logger.info(f"Successfully scraped {self.base_url}")
            return brand_context
            
        except Exception as e:
            logger.error(f"Error scraping {self.base_url}: {str(e)}")
            return BrandContext(
                website_url=self.base_url,
                extracted_at=datetime.now(),
                extraction_status="error",
                error_message=str(e)
            )
    
    def _get_page_soup(self, url: str) -> Optional[BeautifulSoup]:
        """Get BeautifulSoup object for a given URL"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def _extract_brand_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract brand name from homepage"""
        try:
            # Try multiple selectors for brand name
            selectors = [
                'title',
                '.site-header__logo img',
                '.header__logo img',
                '.logo img',
                'h1.site-title',
                '.brand-name'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    if element.name == 'img' and element.get('alt'):
                        return element.get('alt').strip()
                    elif element.name == 'title':
                        title = element.get_text().strip()
                        # Remove common suffixes
                        for suffix in [' - Online Store', ' | Shopify', ' Store']:
                            title = title.replace(suffix, '')
                        return title.strip()
                    else:
                        return element.get_text().strip()
            
            # Fallback to domain name
            domain = urlparse(self.base_url).netloc
            return domain.replace('www.', '').split('.')[0].title()
            
        except Exception as e:
            logger.error(f"Error extracting brand name: {str(e)}")
            return None
    
    def _extract_product_catalog(self) -> List[Product]:
        """Extract product catalog using products.json endpoint"""
        products = []
        try:
            page = 1
            while True:
                url = f"{self.base_url}/products.json?page={page}&limit=250"
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                if not data.get('products'):
                    break
                
                for product_data in data['products']:
                    try:
                        product = Product(
                            id=product_data.get('id'),
                            title=product_data.get('title', ''),
                            handle=product_data.get('handle'),
                            vendor=product_data.get('vendor'),
                            product_type=product_data.get('product_type'),
                            tags=product_data.get('tags', []) if isinstance(product_data.get('tags'), list) else product_data.get('tags', '').split(',') if product_data.get('tags') else [],
                            images=[img.get('src') for img in product_data.get('images', []) if img.get('src')],
                            variants=product_data.get('variants', []),
                            available=any(v.get('available', False) for v in product_data.get('variants', [])),
                            description=product_data.get('body_html', '').strip()
                        )
                        
                        # Extract price from first available variant
                        variants = product_data.get('variants', [])
                        if variants:
                            variant = variants[0]
                            product.price = variant.get('price')
                            product.compare_at_price = variant.get('compare_at_price')
                        
                        products.append(product)
                        
                    except Exception as e:
                        logger.error(f"Error parsing product {product_data.get('id', 'unknown')}: {str(e)}")
                        continue
                
                # Check if there are more pages
                if len(data['products']) < 250:
                    break
                page += 1
                
        except Exception as e:
            logger.error(f"Error fetching product catalog: {str(e)}")
        
        return products
    
    def _extract_hero_products(self, soup: BeautifulSoup) -> List[Product]:
        """Extract hero products from homepage"""
        hero_products = []
        try:
            # Look for product links on homepage
            product_selectors = [
                '.product-card a[href*="/products/"]',
                '.featured-product a[href*="/products/"]',
                '.product-item a[href*="/products/"]',
                'a[href*="/products/"]'
            ]
            
            product_links = set()
            for selector in product_selectors:
                elements = soup.select(selector)
                for element in elements[:10]:  # Limit to first 10
                    href = element.get('href')
                    if href and '/products/' in href:
                        product_links.add(urljoin(self.base_url, href))
            
            # Extract product details for each hero product
            for product_url in list(product_links)[:5]:  # Limit to 5 hero products
                try:
                    # Try to get product handle from URL
                    handle = product_url.split('/products/')[-1].split('?')[0]
                    
                    # Fetch product page
                    product_soup = self._get_page_soup(product_url)
                    if product_soup:
                        product = self._extract_product_from_page(product_soup, handle)
                        if product:
                            hero_products.append(product)
                            
                except Exception as e:
                    logger.error(f"Error extracting hero product from {product_url}: {str(e)}")
                    continue
        
        except Exception as e:
            logger.error(f"Error extracting hero products: {str(e)}")
        
        return hero_products
    
    def _extract_product_from_page(self, soup: BeautifulSoup, handle: str) -> Optional[Product]:
        """Extract product details from product page"""
        try:
            # Extract title
            title_selectors = [
                '.product-title',
                '.product__title',
                'h1.product-single__title',
                'h1'
            ]
            title = None
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element:
                    title = element.get_text().strip()
                    break
            
            if not title:
                return None
            
            # Extract price
            price_selectors = [
                '.price',
                '.product-price',
                '.product__price',
                '[data-price]'
            ]
            price = None
            for selector in price_selectors:
                element = soup.select_one(selector)
                if element:
                    price_text = element.get_text().strip()
                    # Extract numerical price
                    price_match = re.search(r'[\d,]+\.?\d*', price_text)
                    if price_match:
                        price = price_match.group()
                        break
            
            # Extract images
            image_selectors = [
                '.product-images img',
                '.product__photos img',
                '.product-photo img'
            ]
            images = []
            for selector in image_selectors:
                elements = soup.select(selector)
                for img in elements:
                    src = img.get('src') or img.get('data-src')
                    if src and 'http' in src:
                        images.append(src)
            
            # Extract description
            desc_selectors = [
                '.product-description',
                '.product__description',
                '.product-single__description'
            ]
            description = None
            for selector in desc_selectors:
                element = soup.select_one(selector)
                if element:
                    description = element.get_text().strip()
                    break
            
            return Product(
                title=title,
                handle=handle,
                price=price,
                images=images,
                description=description
            )
            
        except Exception as e:
            logger.error(f"Error extracting product from page: {str(e)}")
            return None
    
    def _extract_policy(self, policy_type: str, soup: BeautifulSoup) -> Optional[Policy]:
        """Extract policy information"""
        try:
            # Common policy URLs
            policy_urls = {
                'privacy': ['/pages/privacy-policy', '/privacy-policy', '/policies/privacy-policy'],
                'return': ['/pages/return-policy', '/return-policy', '/policies/refund-policy', '/pages/refund-policy']
            }
            
            # Try to find policy link in footer or navigation
            policy_links = []
            if policy_type in policy_urls:
                for path in policy_urls[policy_type]:
                    policy_links.append(urljoin(self.base_url, path))
            
            # Also search for links on the page
            search_terms = {
                'privacy': ['privacy', 'privacy policy'],
                'return': ['return', 'refund', 'return policy', 'refund policy']
            }
            
            if policy_type in search_terms:
                for term in search_terms[policy_type]:
                    links = soup.find_all('a', string=re.compile(term, re.IGNORECASE))
                    for link in links:
                        href = link.get('href')
                        if href:
                            policy_links.append(urljoin(self.base_url, href))
            
            # Try each policy URL
            for policy_url in policy_links[:3]:  # Limit to first 3 attempts
                try:
                    policy_soup = self._get_page_soup(policy_url)
                    if policy_soup:
                        # Extract policy content
                        content_selectors = [
                            '.page-content',
                            '.rte',
                            '.policy-content',
                            '.page__content',
                            'main'
                        ]
                        
                        content = None
                        for selector in content_selectors:
                            element = policy_soup.select_one(selector)
                            if element:
                                content = element.get_text().strip()
                                break
                        
                        if content and len(content) > 100:  # Ensure substantial content
                            title = f"{policy_type.title()} Policy"
                            return Policy(
                                title=title,
                                content=content[:2000],  # Limit content length
                                url=policy_url
                            )
                            
                except Exception as e:
                    logger.error(f"Error extracting policy from {policy_url}: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Error extracting {policy_type} policy: {str(e)}")
        
        return None
    
    def _extract_faqs(self, soup: BeautifulSoup) -> List[FAQ]:
        """Extract FAQ information"""
        faqs = []
        try:
            # Try to find FAQ page
            faq_links = []
            faq_terms = ['faq', 'frequently asked questions', 'help', 'support']
            
            for term in faq_terms:
                links = soup.find_all('a', string=re.compile(term, re.IGNORECASE))
                for link in links:
                    href = link.get('href')
                    if href:
                        faq_links.append(urljoin(self.base_url, href))
            
            # Also try common FAQ URLs
            common_faq_urls = ['/pages/faq', '/faq', '/help', '/support']
            for path in common_faq_urls:
                faq_links.append(urljoin(self.base_url, path))
            
            # Try each FAQ URL
            for faq_url in faq_links[:3]:
                try:
                    faq_soup = self._get_page_soup(faq_url)
                    if faq_soup:
                        # Look for FAQ patterns
                        faq_patterns = [
                            ('.faq-item', '.faq-question', '.faq-answer'),
                            ('.accordion-item', '.accordion-header', '.accordion-body'),
                            ('.question', None, '.answer'),
                            ('dt', None, 'dd')
                        ]
                        
                        for container_selector, question_selector, answer_selector in faq_patterns:
                            containers = faq_soup.select(container_selector)
                            
                            for container in containers:
                                try:
                                    if question_selector and answer_selector:
                                        question_elem = container.select_one(question_selector)
                                        answer_elem = container.select_one(answer_selector)
                                    elif container_selector == 'dt':
                                        question_elem = container
                                        answer_elem = container.find_next_sibling('dd')
                                    else:
                                        # Try to find question and answer within container
                                        question_elem = container.find(['h1', 'h2', 'h3', 'h4', 'strong', 'b'])
                                        answer_elem = container
                                    
                                    if question_elem and answer_elem:
                                        question = question_elem.get_text().strip()
                                        answer = answer_elem.get_text().strip()
                                        
                                        # Clean up answer text
                                        if question in answer:
                                            answer = answer.replace(question, '').strip()
                                        
                                        if question and answer and len(question) > 5 and len(answer) > 10:
                                            faqs.append(FAQ(question=question, answer=answer))
                                            
                                except Exception as e:
                                    continue
                        
                        if faqs:
                            break
                            
                except Exception as e:
                    logger.error(f"Error extracting FAQs from {faq_url}: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Error extracting FAQs: {str(e)}")
        
        return faqs[:10]  # Limit to 10 FAQs
    
    def _extract_social_handles(self, soup: BeautifulSoup) -> List[SocialHandle]:
        """Extract social media handles"""
        social_handles = []
        try:
            # Common social media platforms and their URL patterns
            social_platforms = {
                'instagram': ['instagram.com', 'instagr.am'],
                'facebook': ['facebook.com', 'fb.com'],
                'twitter': ['twitter.com', 't.co'],
                'tiktok': ['tiktok.com'],
                'youtube': ['youtube.com', 'youtu.be'],
                'linkedin': ['linkedin.com'],
                'pinterest': ['pinterest.com']
            }
            
            # Find all links
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href', '').lower()
                
                for platform, domains in social_platforms.items():
                    for domain in domains:
                        if domain in href:
                            # Extract handle from URL
                            handle = None
                            url_parts = href.split('/')
                            
                            if platform == 'instagram':
                                # Instagram handle is usually after instagram.com/
                                for i, part in enumerate(url_parts):
                                    if 'instagram.com' in part and i + 1 < len(url_parts):
                                        handle = url_parts[i + 1].split('?')[0]
                                        break
                            elif platform == 'facebook':
                                # Facebook handle/page
                                for i, part in enumerate(url_parts):
                                    if 'facebook.com' in part and i + 1 < len(url_parts):
                                        handle = url_parts[i + 1].split('?')[0]
                                        break
                            elif platform == 'twitter':
                                # Twitter handle
                                for i, part in enumerate(url_parts):
                                    if 'twitter.com' in part and i + 1 < len(url_parts):
                                        handle = url_parts[i + 1].split('?')[0]
                                        break
                            
                            social_handles.append(SocialHandle(
                                platform=platform,
                                url=link.get('href'),
                                handle=handle
                            ))
                            break
            
            # Remove duplicates
            seen_urls = set()
            unique_handles = []
            for handle in social_handles:
                if handle.url not in seen_urls:
                    seen_urls.add(handle.url)
                    unique_handles.append(handle)
            
        except Exception as e:
            logger.error(f"Error extracting social handles: {str(e)}")
        
        return unique_handles
    
    def _extract_contact_info(self, soup: BeautifulSoup) -> ContactInfo:
        """Extract contact information"""
        contact_info = ContactInfo()
        try:
            page_text = soup.get_text()
            
            # Extract emails using regex
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, page_text)
            contact_info.emails = list(set(emails))  # Remove duplicates
            
            # Extract phone numbers using regex
            phone_patterns = [
                r'\+\d{1,3}[\s-]?\d{3,14}',  # International format
                r'\(\d{3}\)[\s-]?\d{3}[\s-]?\d{4}',  # US format (xxx) xxx-xxxx
                r'\d{3}[\s-]?\d{3}[\s-]?\d{4}',  # US format xxx-xxx-xxxx
                r'\d{10,}',  # Simple long number
            ]
            
            phones = []
            for pattern in phone_patterns:
                matches = re.findall(pattern, page_text)
                phones.extend(matches)
            
            # Filter valid phone numbers (remove numbers that are too short or likely not phones)
            valid_phones = []
            for phone in phones:
                clean_phone = re.sub(r'[^\d]', '', phone)
                if 10 <= len(clean_phone) <= 15:
                    valid_phones.append(phone)
            
            contact_info.phones = list(set(valid_phones))
            
            # Try to find contact page for more information
            contact_links = []
            contact_terms = ['contact', 'contact us', 'get in touch']
            
            for term in contact_terms:
                links = soup.find_all('a', string=re.compile(term, re.IGNORECASE))
                for link in links:
                    href = link.get('href')
                    if href:
                        contact_links.append(urljoin(self.base_url, href))
            
            # Also try common contact URLs
            common_contact_urls = ['/pages/contact', '/contact', '/contact-us']
            for path in common_contact_urls:
                contact_links.append(urljoin(self.base_url, path))
            
            # Extract additional contact info from contact pages
            for contact_url in contact_links[:2]:  # Limit to 2 attempts
                try:
                    contact_soup = self._get_page_soup(contact_url)
                    if contact_soup:
                        contact_text = contact_soup.get_text()
                        
                        # Extract additional emails and phones
                        additional_emails = re.findall(email_pattern, contact_text)
                        contact_info.emails.extend(additional_emails)
                        
                        for pattern in phone_patterns:
                            matches = re.findall(pattern, contact_text)
                            for phone in matches:
                                clean_phone = re.sub(r'[^\d]', '', phone)
                                if 10 <= len(clean_phone) <= 15:
                                    contact_info.phones.append(phone)
                        
                        break
                        
                except Exception as e:
                    logger.error(f"Error extracting contact info from {contact_url}: {str(e)}")
                    continue
            
            # Remove duplicates
            contact_info.emails = list(set(contact_info.emails))
            contact_info.phones = list(set(contact_info.phones))
            
        except Exception as e:
            logger.error(f"Error extracting contact info: {str(e)}")
        
        return contact_info
    
    def _extract_about_brand(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract brand context/about information"""
        try:
            # Try to find about page
            about_links = []
            about_terms = ['about', 'about us', 'our story', 'who we are']
            
            for term in about_terms:
                links = soup.find_all('a', string=re.compile(term, re.IGNORECASE))
                for link in links:
                    href = link.get('href')
                    if href:
                        about_links.append(urljoin(self.base_url, href))
            
            # Also try common about URLs
            common_about_urls = ['/pages/about', '/about', '/pages/about-us', '/our-story']
            for path in common_about_urls:
                about_links.append(urljoin(self.base_url, path))
            
            # Try each about URL
            for about_url in about_links[:3]:
                try:
                    about_soup = self._get_page_soup(about_url)
                    if about_soup:
                        # Extract main content
                        content_selectors = [
                            '.page-content',
                            '.rte',
                            '.about-content',
                            '.page__content',
                            'main'
                        ]
                        
                        for selector in content_selectors:
                            element = about_soup.select_one(selector)
                            if element:
                                content = element.get_text().strip()
                                if len(content) > 100:  # Ensure substantial content
                                    return content[:1000]  # Limit content length
                        
                        # Fallback: use trafilatura for better text extraction
                        try:
                            response = self.session.get(about_url, timeout=30)
                            if response.status_code == 200:
                                extracted_text = trafilatura.extract(response.content)
                                if extracted_text and len(extracted_text) > 100:
                                    return extracted_text[:1000]
                        except:
                            pass
                            
                except Exception as e:
                    logger.error(f"Error extracting about info from {about_url}: {str(e)}")
                    continue
            
            # Fallback: look for description meta tags or homepage content
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                return meta_desc.get('content').strip()
            
        except Exception as e:
            logger.error(f"Error extracting about brand: {str(e)}")
        
        return None
    
    def _extract_important_links(self, soup: BeautifulSoup) -> List[ImportantLink]:
        """Extract important links"""
        important_links = []
        try:
            # Define important link patterns
            important_patterns = {
                'order tracking': ['track', 'order tracking', 'track order', 'track your order'],
                'contact us': ['contact', 'contact us', 'get in touch'],
                'blog': ['blog', 'news', 'articles'],
                'size guide': ['size guide', 'sizing', 'size chart'],
                'shipping': ['shipping', 'delivery'],
                'returns': ['returns', 'return policy'],
                'help': ['help', 'support', 'customer service']
            }
            
            # Find links in navigation, footer, and main content
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href')
                text = link.get_text().strip().lower()
                
                if href and text:
                    for category, patterns in important_patterns.items():
                        for pattern in patterns:
                            if pattern in text and len(text) < 100:  # Avoid very long link texts
                                full_url = urljoin(self.base_url, href)
                                
                                important_links.append(ImportantLink(
                                    title=link.get_text().strip(),
                                    url=full_url,
                                    description=category
                                ))
                                break
                        else:
                            continue
                        break  # Found match, break outer loop
            
            # Remove duplicates based on URL
            seen_urls = set()
            unique_links = []
            for link in important_links:
                if link.url not in seen_urls:
                    seen_urls.add(link.url)
                    unique_links.append(link)
            
        except Exception as e:
            logger.error(f"Error extracting important links: {str(e)}")
        
        return unique_links[:10]  # Limit to 10 links

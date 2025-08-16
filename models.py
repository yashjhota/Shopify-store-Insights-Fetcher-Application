from pydantic import BaseModel, HttpUrl, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class Product(BaseModel):
    """Model for individual product data"""
    id: Optional[int] = None
    title: str
    handle: Optional[str] = None
    price: Optional[str] = None
    compare_at_price: Optional[str] = None
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    tags: Optional[List[str]] = []
    images: Optional[List[str]] = []
    variants: Optional[List[Dict[str, Any]]] = []
    available: Optional[bool] = True
    description: Optional[str] = None

class FAQ(BaseModel):
    """Model for FAQ data"""
    question: str
    answer: str

class SocialHandle(BaseModel):
    """Model for social media handles"""
    platform: str
    url: str
    handle: Optional[str] = None

class ContactInfo(BaseModel):
    """Model for contact information"""
    emails: List[str] = []
    phones: List[str] = []
    addresses: List[str] = []

class Policy(BaseModel):
    """Model for policy information"""
    title: str
    content: str
    url: Optional[str] = None

class ImportantLink(BaseModel):
    """Model for important links"""
    title: str
    url: str
    description: Optional[str] = None

class BrandContext(BaseModel):
    """Main model for brand data extracted from Shopify store"""
    website_url: str
    brand_name: Optional[str] = None
    
    # Product information
    product_catalog: List[Product] = []
    hero_products: List[Product] = []
    
    # Policies
    privacy_policy: Optional[Policy] = None
    return_refund_policy: Optional[Policy] = None
    
    # FAQ
    faqs: List[FAQ] = []
    
    # Social and contact
    social_handles: List[SocialHandle] = []
    contact_info: ContactInfo = ContactInfo()
    
    # Brand information
    about_brand: Optional[str] = None
    
    # Important links
    important_links: List[ImportantLink] = []
    
    # Metadata
    extracted_at: datetime
    extraction_status: str = "success"
    error_message: Optional[str] = None

class ScrapingRequest(BaseModel):
    """Model for API request"""
    website_url: HttpUrl
    
    @validator('website_url')
    def validate_url(cls, v):
        url_str = str(v)
        if not (url_str.startswith('http://') or url_str.startswith('https://')):
            raise ValueError('URL must include protocol (http:// or https://)')
        return url_str

class ErrorResponse(BaseModel):
    """Model for error responses"""
    error: str
    status_code: int
    message: str
    timestamp: datetime

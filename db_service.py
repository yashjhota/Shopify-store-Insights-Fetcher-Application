"""Database service layer for persisting scraped data"""
import json
import logging
from app import db
from db_models import (
    Brand, Product, HeroProduct, PolicyData, FAQData, SocialHandle, 
    ContactInfo, ImportantLink, Competitor, CompetitorAnalysisJob
)
from models import BrandContext
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service class for database operations"""
    
    @staticmethod
    def save_brand_data(brand_context: BrandContext) -> Brand:
        """Save complete brand data to database"""
        try:
            # Check if brand already exists
            existing_brand = Brand.query.filter_by(website_url=brand_context.website_url).first()
            
            if existing_brand:
                # Update existing brand
                brand = existing_brand
                # Clear existing data to avoid duplicates
                DatabaseService._clear_brand_data(brand)
            else:
                # Create new brand
                brand = Brand()
                db.session.add(brand)
            
            # Update brand basic info
            brand.website_url = brand_context.website_url
            brand.brand_name = brand_context.brand_name
            brand.about_brand = brand_context.about_brand
            brand.extraction_status = brand_context.extraction_status
            brand.error_message = brand_context.error_message
            brand.extracted_at = brand_context.extracted_at
            
            # Save products
            for product_data in brand_context.product_catalog:
                product = Product(
                    brand=brand,
                    shopify_id=product_data.id,
                    title=product_data.title,
                    handle=product_data.handle,
                    price=product_data.price,
                    compare_at_price=product_data.compare_at_price,
                    vendor=product_data.vendor,
                    product_type=product_data.product_type,
                    tags=json.dumps(product_data.tags) if product_data.tags else None,
                    images=json.dumps(product_data.images) if product_data.images else None,
                    variants=json.dumps(product_data.variants) if product_data.variants else None,
                    available=product_data.available,
                    description=product_data.description
                )
                db.session.add(product)
            
            # Save hero products
            for hero_data in brand_context.hero_products:
                hero = HeroProduct(
                    brand=brand,
                    title=hero_data.title,
                    handle=hero_data.handle,
                    price=hero_data.price,
                    images=json.dumps(hero_data.images) if hero_data.images else None,
                    description=hero_data.description
                )
                db.session.add(hero)
            
            # Save policies
            if brand_context.privacy_policy:
                policy = PolicyData(
                    brand=brand,
                    policy_type='privacy',
                    title=brand_context.privacy_policy.title,
                    content=brand_context.privacy_policy.content,
                    url=brand_context.privacy_policy.url
                )
                db.session.add(policy)
            
            if brand_context.return_refund_policy:
                policy = PolicyData(
                    brand=brand,
                    policy_type='return',
                    title=brand_context.return_refund_policy.title,
                    content=brand_context.return_refund_policy.content,
                    url=brand_context.return_refund_policy.url
                )
                db.session.add(policy)
            
            # Save FAQs
            for faq_data in brand_context.faqs:
                faq = FAQData(
                    brand=brand,
                    question=faq_data.question,
                    answer=faq_data.answer
                )
                db.session.add(faq)
            
            # Save social handles
            for social_data in brand_context.social_handles:
                social = SocialHandle(
                    brand=brand,
                    platform=social_data.platform,
                    url=social_data.url,
                    handle=social_data.handle
                )
                db.session.add(social)
            
            # Save contact info
            if brand_context.contact_info:
                contact = ContactInfo(
                    brand=brand,
                    emails=json.dumps(brand_context.contact_info.emails) if brand_context.contact_info.emails else None,
                    phones=json.dumps(brand_context.contact_info.phones) if brand_context.contact_info.phones else None,
                    addresses=json.dumps(brand_context.contact_info.addresses) if brand_context.contact_info.addresses else None
                )
                db.session.add(contact)
            
            # Save important links
            for link_data in brand_context.important_links:
                link = ImportantLink(
                    brand=brand,
                    title=link_data.title,
                    url=link_data.url,
                    description=link_data.description
                )
                db.session.add(link)
            
            db.session.commit()
            logger.info(f"Successfully saved brand data for {brand.website_url}")
            return brand
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving brand data: {str(e)}")
            raise e
    
    @staticmethod
    def _clear_brand_data(brand: Brand):
        """Clear existing data for a brand (for updates)"""
        try:
            # Delete related data
            Product.query.filter_by(brand_id=brand.id).delete()
            HeroProduct.query.filter_by(brand_id=brand.id).delete()
            PolicyData.query.filter_by(brand_id=brand.id).delete()
            FAQData.query.filter_by(brand_id=brand.id).delete()
            SocialHandle.query.filter_by(brand_id=brand.id).delete()
            ContactInfo.query.filter_by(brand_id=brand.id).delete()
            ImportantLink.query.filter_by(brand_id=brand.id).delete()
            
        except Exception as e:
            logger.error(f"Error clearing brand data: {str(e)}")
            raise e
    
    @staticmethod
    def get_brand_by_url(website_url: str) -> Optional[Brand]:
        """Get brand by website URL"""
        return Brand.query.filter_by(website_url=website_url).first()
    
    @staticmethod
    def get_all_brands() -> List[Brand]:
        """Get all brands from database"""
        return Brand.query.all()
    
    @staticmethod
    def add_competitor_relationship(brand_id: int, competitor_brand_id: int, 
                                  discovered_via: str = 'web_search', 
                                  similarity_score: float = None):
        """Add competitor relationship between brands"""
        try:
            # Check if relationship already exists
            existing = Competitor.query.filter_by(
                brand_id=brand_id, 
                competitor_brand_id=competitor_brand_id
            ).first()
            
            if not existing:
                competitor = Competitor(
                    brand_id=brand_id,
                    competitor_brand_id=competitor_brand_id,
                    discovered_via=discovered_via,
                    similarity_score=similarity_score
                )
                db.session.add(competitor)
                db.session.commit()
                logger.info(f"Added competitor relationship: {brand_id} -> {competitor_brand_id}")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding competitor relationship: {str(e)}")
            raise e
    
    @staticmethod
    def get_competitors(brand_id: int) -> List[Brand]:
        """Get competitors for a brand"""
        competitor_relationships = Competitor.query.filter_by(brand_id=brand_id).all()
        return [rel.competitor_brand for rel in competitor_relationships]
    
    @staticmethod
    def create_competitor_analysis_job(brand_id: int) -> CompetitorAnalysisJob:
        """Create a new competitor analysis job"""
        try:
            job = CompetitorAnalysisJob(
                brand_id=brand_id,
                status='pending'
            )
            db.session.add(job)
            db.session.commit()
            return job
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating competitor analysis job: {str(e)}")
            raise e
    
    @staticmethod
    def update_competitor_job_status(job_id: int, status: str, 
                                   competitors_found: int = None, 
                                   error_message: str = None):
        """Update competitor analysis job status"""
        try:
            job = CompetitorAnalysisJob.query.get(job_id)
            if job:
                job.status = status
                if competitors_found is not None:
                    job.competitors_found = competitors_found
                if error_message:
                    job.error_message = error_message
                if status in ['completed', 'failed']:
                    job.completed_at = datetime.utcnow()
                
                db.session.commit()
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating competitor job status: {str(e)}")
            raise e
    
    @staticmethod
    def brand_to_dict(brand: Brand) -> dict:
        """Convert Brand model to dictionary for API response"""
        try:
            # Get related data
            products = Product.query.filter_by(brand_id=brand.id).all()
            hero_products = HeroProduct.query.filter_by(brand_id=brand.id).all()
            policies = PolicyData.query.filter_by(brand_id=brand.id).all()
            faqs = FAQData.query.filter_by(brand_id=brand.id).all()
            social_handles = SocialHandle.query.filter_by(brand_id=brand.id).all()
            contact_info = ContactInfo.query.filter_by(brand_id=brand.id).first()
            important_links = ImportantLink.query.filter_by(brand_id=brand.id).all()
            competitors = DatabaseService.get_competitors(brand.id)
            
            return {
                'id': brand.id,
                'website_url': brand.website_url,
                'brand_name': brand.brand_name,
                'about_brand': brand.about_brand,
                'extraction_status': brand.extraction_status,
                'error_message': brand.error_message,
                'extracted_at': brand.extracted_at.isoformat() if brand.extracted_at else None,
                'product_catalog': [
                    {
                        'id': p.shopify_id,
                        'title': p.title,
                        'handle': p.handle,
                        'price': p.price,
                        'compare_at_price': p.compare_at_price,
                        'vendor': p.vendor,
                        'product_type': p.product_type,
                        'tags': json.loads(p.tags) if p.tags else [],
                        'images': json.loads(p.images) if p.images else [],
                        'variants': json.loads(p.variants) if p.variants else [],
                        'available': p.available,
                        'description': p.description
                    } for p in products
                ],
                'hero_products': [
                    {
                        'title': hp.title,
                        'handle': hp.handle,
                        'price': hp.price,
                        'images': json.loads(hp.images) if hp.images else [],
                        'description': hp.description
                    } for hp in hero_products
                ],
                'privacy_policy': next(
                    ({
                        'title': p.title,
                        'content': p.content,
                        'url': p.url
                    } for p in policies if p.policy_type == 'privacy'), None
                ),
                'return_refund_policy': next(
                    ({
                        'title': p.title,
                        'content': p.content,
                        'url': p.url
                    } for p in policies if p.policy_type == 'return'), None
                ),
                'faqs': [
                    {
                        'question': f.question,
                        'answer': f.answer
                    } for f in faqs
                ],
                'social_handles': [
                    {
                        'platform': sh.platform,
                        'url': sh.url,
                        'handle': sh.handle
                    } for sh in social_handles
                ],
                'contact_info': {
                    'emails': json.loads(contact_info.emails) if contact_info and contact_info.emails else [],
                    'phones': json.loads(contact_info.phones) if contact_info and contact_info.phones else [],
                    'addresses': json.loads(contact_info.addresses) if contact_info and contact_info.addresses else []
                } if contact_info else {'emails': [], 'phones': [], 'addresses': []},
                'important_links': [
                    {
                        'title': il.title,
                        'url': il.url,
                        'description': il.description
                    } for il in important_links
                ],
                'competitors': [
                    {
                        'id': c.id,
                        'brand_name': c.brand_name,
                        'website_url': c.website_url,
                        'extracted_at': c.extracted_at.isoformat() if c.extracted_at else None
                    } for c in competitors
                ]
            }
            
        except Exception as e:
            logger.error(f"Error converting brand to dict: {str(e)}")
            return {}
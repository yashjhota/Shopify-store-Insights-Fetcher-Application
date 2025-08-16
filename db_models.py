from app import db
from datetime import datetime
import json

class Brand(db.Model):
    """Model for storing brand/store information"""
    __tablename__ = 'brands'
    
    id = db.Column(db.Integer, primary_key=True)
    website_url = db.Column(db.String(500), nullable=False, unique=True)
    brand_name = db.Column(db.String(200))
    about_brand = db.Column(db.Text)
    extraction_status = db.Column(db.String(50), default='success')
    error_message = db.Column(db.Text)
    extracted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='brand', lazy=True, cascade='all, delete-orphan')
    hero_products = db.relationship('HeroProduct', backref='brand', lazy=True, cascade='all, delete-orphan')
    policies = db.relationship('PolicyData', backref='brand', lazy=True, cascade='all, delete-orphan')
    faqs = db.relationship('FAQData', backref='brand', lazy=True, cascade='all, delete-orphan')
    social_handles = db.relationship('SocialHandle', backref='brand', lazy=True, cascade='all, delete-orphan')
    contact_info = db.relationship('ContactInfo', backref='brand', lazy=True, uselist=False, cascade='all, delete-orphan')
    important_links = db.relationship('ImportantLink', backref='brand', lazy=True, cascade='all, delete-orphan')
    competitors = db.relationship('Competitor', foreign_keys='Competitor.brand_id', backref='brand', lazy=True, cascade='all, delete-orphan')

class Product(db.Model):
    """Model for storing product information"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    shopify_id = db.Column(db.BigInteger)
    title = db.Column(db.String(500), nullable=False)
    handle = db.Column(db.String(200))
    price = db.Column(db.String(50))
    compare_at_price = db.Column(db.String(50))
    vendor = db.Column(db.String(200))
    product_type = db.Column(db.String(200))
    tags = db.Column(db.Text)  # JSON string
    images = db.Column(db.Text)  # JSON string
    variants = db.Column(db.Text)  # JSON string
    available = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class HeroProduct(db.Model):
    """Model for storing hero products displayed on homepage"""
    __tablename__ = 'hero_products'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    handle = db.Column(db.String(200))
    price = db.Column(db.String(50))
    images = db.Column(db.Text)  # JSON string
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PolicyData(db.Model):
    """Model for storing policy information"""
    __tablename__ = 'policies'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    policy_type = db.Column(db.String(50), nullable=False)  # 'privacy', 'return', etc.
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FAQData(db.Model):
    """Model for storing FAQ information"""
    __tablename__ = 'faqs'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SocialHandle(db.Model):
    """Model for storing social media handles"""
    __tablename__ = 'social_handles'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    handle = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ContactInfo(db.Model):
    """Model for storing contact information"""
    __tablename__ = 'contact_info'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    emails = db.Column(db.Text)  # JSON string
    phones = db.Column(db.Text)  # JSON string
    addresses = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ImportantLink(db.Model):
    """Model for storing important links"""
    __tablename__ = 'important_links'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Competitor(db.Model):
    """Model for storing competitor relationships"""
    __tablename__ = 'competitors'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    competitor_brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    similarity_score = db.Column(db.Float)  # Optional scoring mechanism
    discovered_via = db.Column(db.String(100))  # 'web_search', 'manual', etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to competitor brand
    competitor_brand = db.relationship('Brand', foreign_keys=[competitor_brand_id])

class CompetitorAnalysisJob(db.Model):
    """Model for tracking competitor analysis jobs"""
    __tablename__ = 'competitor_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, running, completed, failed
    competitors_found = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
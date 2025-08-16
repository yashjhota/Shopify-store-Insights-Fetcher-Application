from flask import render_template, request, jsonify, url_for, redirect, flash
from app import app
from models import ScrapingRequest, BrandContext, ErrorResponse
from scraper import ShopifyScraper
from datetime import datetime
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Homepage with scraping interface"""
    return render_template('index.html')

@app.route('/api/scrape', methods=['POST'])
def scrape_store():
    """API endpoint to scrape Shopify store"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify(ErrorResponse(
                error="Invalid request",
                status_code=400,
                message="Request body must contain valid JSON",
                timestamp=datetime.now()
            ).dict()), 400
        
        # Validate request data
        try:
            scraping_request = ScrapingRequest(**data)
        except ValidationError as e:
            return jsonify(ErrorResponse(
                error="Validation error",
                status_code=400,
                message=f"Invalid request data: {str(e)}",
                timestamp=datetime.now()
            ).dict()), 400
        
        website_url = str(scraping_request.website_url)
        logger.info(f"Starting scraping process for: {website_url}")
        
        # Check if URL is accessible
        try:
            import requests
            response = requests.head(str(website_url), timeout=10)
            if response.status_code == 404:
                return jsonify(ErrorResponse(
                    error="Website not found",
                    status_code=401,
                    message=f"Website {website_url} was not found or is not accessible",
                    timestamp=datetime.now()
                ).dict()), 401
        except requests.exceptions.RequestException:
            return jsonify(ErrorResponse(
                error="Website not accessible",
                status_code=401,
                message=f"Website {website_url} is not accessible",
                timestamp=datetime.now()
            ).dict()), 401
        
        # Initialize scraper and scrape the store
        scraper = ShopifyScraper(website_url)
        brand_context = scraper.scrape_store()
        
        # Check if scraping was successful
        if brand_context.extraction_status == "error":
            return jsonify(ErrorResponse(
                error="Scraping failed",
                status_code=500,
                message=brand_context.error_message or "Internal error occurred during scraping",
                timestamp=datetime.now()
            ).dict()), 500
        
        # Return successful response
        return jsonify(brand_context.dict()), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in scrape_store: {str(e)}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            status_code=500,
            message="An unexpected error occurred",
            timestamp=datetime.now()
        ).dict()), 500

@app.route('/scrape', methods=['POST'])
def scrape_form():
    """Form-based scraping endpoint for web interface"""
    try:
        website_url = request.form.get('website_url')
        
        if not website_url:
            flash('Please enter a website URL', 'error')
            return redirect(url_for('index'))
        
        # Add protocol if missing
        if not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url
        
        # Validate URL
        try:
            from pydantic import HttpUrl
            scraping_request = ScrapingRequest(website_url=HttpUrl(website_url))
        except ValidationError as e:
            flash(f'Invalid URL: {str(e)}', 'error')
            return redirect(url_for('index'))
        
        # Initialize scraper and scrape the store
        scraper = ShopifyScraper(str(website_url))
        brand_context = scraper.scrape_store()
        
        return render_template('results.html', brand_context=brand_context)
        
    except Exception as e:
        logger.error(f"Error in scrape_form: {str(e)}")
        flash('An error occurred while scraping the website', 'error')
        return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return jsonify(ErrorResponse(
        error="Not found",
        status_code=404,
        message="The requested resource was not found",
        timestamp=datetime.now()
    ).dict()), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify(ErrorResponse(
        error="Internal server error",
        status_code=500,
        message="An internal server error occurred",
        timestamp=datetime.now()
    ).dict()), 500

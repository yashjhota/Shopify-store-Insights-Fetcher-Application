from flask import render_template, request, jsonify, url_for, redirect, flash
from app import app
from models import ScrapingRequest, BrandContext, ErrorResponse
from scraper import ShopifyScraper
from datetime import datetime
from pydantic import ValidationError
from db_service import DatabaseService
from competitor_analysis import CompetitorAnalyzer
import logging
import threading
import requests

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
        
        # Save data to database
        try:
            brand = DatabaseService.save_brand_data(brand_context)
            logger.info(f"Saved brand data to database with ID: {brand.id}")
        except Exception as e:
            logger.error(f"Error saving to database: {str(e)}")
            # Continue without failing the request
        
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
        include_competitors = request.form.get('include_competitors', 'false').lower() == 'true'
        
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
        
        # Check if scraping was successful
        if brand_context.extraction_status == "error":
            flash(f'Scraping failed: {brand_context.error_message}', 'error')
            return redirect(url_for('index'))
        
        # Save data to database
        try:
            brand = DatabaseService.save_brand_data(brand_context)
            logger.info(f"Saved brand data to database with ID: {brand.id}")
        except Exception as e:
            logger.error(f"Error saving to database: {str(e)}")
            flash('Error saving data to database', 'error')
            return redirect(url_for('index'))
        
        # Start competitor analysis if requested
        if include_competitors:
            try:
                analyzer = CompetitorAnalyzer()
                
                def run_competitor_analysis():
                    with app.app_context():
                        try:
                            analyzer.analyze_competitors_for_brand(brand.id)
                        except Exception as e:
                            logger.error(f"Background competitor analysis failed: {str(e)}")
                
                # Start analysis in background thread
                thread = threading.Thread(target=run_competitor_analysis)
                thread.daemon = True
                thread.start()
                
                flash('Store analysis completed! Competitor analysis is running in background.', 'success')
                return redirect(url_for('competitor_analysis_ui', brand_id=brand.id))
                
            except Exception as e:
                logger.error(f"Error starting competitor analysis: {str(e)}")
                flash('Store analysis completed, but competitor analysis failed to start', 'warning')
                return render_template('results.html', brand_context=brand_context)
        
        flash('Store analysis completed successfully!', 'success')
        return render_template('results.html', brand_context=brand_context)
        
    except Exception as e:
        logger.error(f"Error in scrape_form: {str(e)}")
        flash('An error occurred while scraping the website', 'error')
        return redirect(url_for('index'))

@app.route('/api/competitors/<int:brand_id>', methods=['POST'])
def analyze_competitors(brand_id):
    """API endpoint to analyze competitors for a brand"""
    try:
        # Get brand from database
        brand = DatabaseService.get_brand_by_url("dummy")  # We'll get by ID instead
        from db_models import Brand
        brand = Brand.query.get(brand_id)
        
        if not brand:
            return jsonify(ErrorResponse(
                error="Brand not found",
                status_code=404,
                message=f"Brand with ID {brand_id} not found",
                timestamp=datetime.now()
            ).dict()), 404
        
        # Start competitor analysis in background
        analyzer = CompetitorAnalyzer()
        
        def run_analysis():
            with app.app_context():
                try:
                    analyzer.analyze_competitors_for_brand(brand_id)
                except Exception as e:
                    logger.error(f"Background competitor analysis failed: {str(e)}")
        
        # Start analysis in background thread
        thread = threading.Thread(target=run_analysis)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "message": "Competitor analysis started",
            "brand_id": brand_id,
            "status": "processing"
        }), 202
        
    except Exception as e:
        logger.error(f"Error starting competitor analysis: {str(e)}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            status_code=500,
            message="Failed to start competitor analysis",
            timestamp=datetime.now()
        ).dict()), 500

@app.route('/api/scrape-with-competitors', methods=['POST'])
def scrape_with_competitors():
    """API endpoint to scrape store and analyze competitors"""
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
        include_competitors = data.get('include_competitors', True)
        
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
        
        # Save data to database
        try:
            brand = DatabaseService.save_brand_data(brand_context)
            logger.info(f"Saved brand data to database with ID: {brand.id}")
        except Exception as e:
            logger.error(f"Error saving to database: {str(e)}")
            return jsonify(ErrorResponse(
                error="Database error",
                status_code=500,
                message="Failed to save brand data",
                timestamp=datetime.now()
            ).dict()), 500
        
        response_data = brand_context.dict()
        response_data['brand_id'] = brand.id
        
        # Start competitor analysis if requested
        if include_competitors:
            try:
                analyzer = CompetitorAnalyzer()
                
                def run_competitor_analysis():
                    with app.app_context():
                        try:
                            analyzer.analyze_competitors_for_brand(brand.id)
                        except Exception as e:
                            logger.error(f"Background competitor analysis failed: {str(e)}")
                
                # Start analysis in background thread
                thread = threading.Thread(target=run_competitor_analysis)
                thread.daemon = True
                thread.start()
                
                response_data['competitor_analysis'] = {
                    'status': 'processing',
                    'message': 'Competitor analysis started in background'
                }
                
            except Exception as e:
                logger.error(f"Error starting competitor analysis: {str(e)}")
                response_data['competitor_analysis'] = {
                    'status': 'failed',
                    'message': 'Failed to start competitor analysis'
                }
        
        # Redirect to competitor analysis UI if this was requested via form
        if request.headers.get('Content-Type') != 'application/json':
            return redirect(url_for('competitor_analysis_ui', brand_id=brand.id))
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in scrape_with_competitors: {str(e)}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            status_code=500,
            message="An unexpected error occurred",
            timestamp=datetime.now()
        ).dict()), 500

@app.route('/api/brands', methods=['GET'])
def get_all_brands():
    """Get all brands from database"""
    try:
        brands = DatabaseService.get_all_brands()
        brands_data = [
            {
                'id': brand.id,
                'brand_name': brand.brand_name,
                'website_url': brand.website_url,
                'extraction_status': brand.extraction_status,
                'extracted_at': brand.extracted_at.isoformat() if brand.extracted_at else None,
                'competitors': [
                    {
                        'id': c.id,
                        'brand_name': c.brand_name,
                        'website_url': c.website_url
                    } for c in DatabaseService.get_competitors(brand.id)
                ]
            } for brand in brands
        ]
        
        return jsonify({
            'brands': brands_data,
            'total': len(brands_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting brands: {str(e)}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            status_code=500,
            message="Failed to retrieve brands",
            timestamp=datetime.now()
        ).dict()), 500

@app.route('/competitor-analysis/<int:brand_id>')
def competitor_analysis_ui(brand_id):
    """Display competitor analysis UI with charts and tables"""
    try:
        from db_models import Brand
        brand = Brand.query.get(brand_id)
        
        if not brand:
            flash(f'Brand with ID {brand_id} not found', 'error')
            return redirect(url_for('index'))
        
        # Get brand data with competitors
        brand_data = DatabaseService.brand_to_dict(brand)
        competitors = brand_data.get('competitors', [])
        
        # Get competitor details for comparison
        competitor_details = []
        for competitor in competitors:
            comp_brand = Brand.query.get(competitor['id'])
            if comp_brand:
                comp_data = DatabaseService.brand_to_dict(comp_brand)
                competitor_details.append(comp_data)
        
        return render_template('competitor_analysis.html', 
                             brand=brand_data, 
                             competitors=competitor_details)
        
    except Exception as e:
        logger.error(f"Error displaying competitor analysis UI: {str(e)}")
        flash('An error occurred while loading competitor analysis', 'error')
        return redirect(url_for('index'))

@app.route('/api/brands/<int:brand_id>', methods=['GET'])
def get_brand_details(brand_id):
    """Get detailed brand information including competitors"""
    try:
        from db_models import Brand
        brand = Brand.query.get(brand_id)
        
        if not brand:
            return jsonify(ErrorResponse(
                error="Brand not found",
                status_code=404,
                message=f"Brand with ID {brand_id} not found",
                timestamp=datetime.now()
            ).dict()), 404
        
        brand_data = DatabaseService.brand_to_dict(brand)
        return jsonify(brand_data), 200
        
    except Exception as e:
        logger.error(f"Error getting brand details: {str(e)}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            status_code=500,
            message="Failed to retrieve brand details",
            timestamp=datetime.now()
        ).dict()), 500

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

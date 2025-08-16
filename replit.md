# Overview

This is a Shopify Store Insights Scraper application built with Flask that extracts comprehensive data from Shopify stores without using the official Shopify API. The application scrapes product catalogs, hero products, policies, FAQs, social handles, contact details, and brand information from any given Shopify store URL and returns structured JSON data.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Web Framework
- **Flask-based REST API** - Lightweight Python web framework chosen for rapid development and simplicity
- **Modular route structure** - Routes separated into dedicated files to avoid circular imports and maintain clean code organization
- **JSON response formatting** - All API responses return structured JSON with proper error handling and status codes

## Data Models
- **Pydantic models** - Type-safe data validation and serialization for all scraped data structures
- **Structured data classes** - Separate models for Product, FAQ, SocialHandle, ContactInfo, Policy, ImportantLink, and main BrandContext
- **Optional field handling** - Graceful handling of missing data with appropriate defaults

## Web Scraping Architecture
- **Multi-source data extraction** - Combines JSON endpoints (like /products.json) with HTML parsing for comprehensive data collection
- **BeautifulSoup HTML parsing** - Robust HTML parsing for extracting unstructured data like FAQs and policies
- **Session-based requests** - Maintains session state with proper user-agent headers to avoid blocking
- **Trafilatura integration** - Advanced text extraction capabilities for clean content parsing

## Error Handling
- **Comprehensive validation** - Request data validation using Pydantic with detailed error messages
- **HTTP status code mapping** - Proper REST API status codes (400 for validation errors, 404 for missing sites, 500 for server errors)
- **Graceful failure handling** - Continues extraction even if some data sources fail

## Frontend Interface
- **Bootstrap dark theme** - Modern, responsive UI with dark theme for better user experience
- **Real-time API testing** - Built-in API testing interface for development and demonstration
- **Loading states and feedback** - Visual feedback during scraping operations with progress indicators

# External Dependencies

## Core Libraries
- **Flask** - Web framework for API endpoints and routing
- **Pydantic** - Data validation and serialization
- **BeautifulSoup4** - HTML parsing and DOM navigation
- **requests** - HTTP client for web scraping
- **trafilatura** - Advanced text extraction from web pages

## Frontend Assets
- **Bootstrap 5** - CSS framework with dark theme variant
- **Font Awesome** - Icon library for UI elements
- **Custom CSS/JS** - Enhanced user experience with loading states and API testing

## Optional Database
- **MySQL support** - Application structured to easily integrate MySQL for data persistence if needed
- **Model-ready architecture** - Pydantic models can be easily adapted for database ORM integration

## Target Platforms
- **Shopify stores** - Specifically designed to extract data from Shopify-powered e-commerce sites
- **JSON API endpoints** - Leverages Shopify's standard /products.json and similar endpoints
- **Standard web scraping** - Falls back to HTML parsing for non-standardized content
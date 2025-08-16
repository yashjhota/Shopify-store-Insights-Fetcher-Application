# 🛍️ Shopify Store Insights-Fetcher Application

🚀 **Unlock the Power of Shopify Data Extraction!** 🚀

A comprehensive Python + Flask application that extracts valuable insights from Shopify stores without using the official Shopify API. This tool provides a robust, scalable solution for gathering store data, including products, policies, FAQs, contact info, and more.


## 🚀 Features

### Mandatory Features (✅ All Implemented)
- **Complete Product Catalog**: Extracts all products using `/products.json` endpoint
- **Hero Products**: Identifies featured products from the homepage
- **Policy Extraction**: Extracts Privacy Policy, Return/Refund policies
- **FAQ Collection**: Gathers frequently asked questions and answers
- **Social Media Handles**: Discovers Instagram, Facebook, TikTok, and other social profiles
- **Contact Information**: Extracts email addresses, phone numbers, and support details
- **Brand Context**: Gets brand description and about information
- **Important Links**: Finds order tracking, contact, blog, and other key pages

### Technical Excellence
- **RESTful API Design**: Clean, well-structured API endpoints
- **Pydantic Models**: Strong data validation and serialization
- **Async Processing**: High-performance async/await implementation
- **Error Handling**: Comprehensive error handling with proper HTTP status codes
- **Clean Architecture**: Modular design following SOLID principles
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- pip package manager

### Quick Start

1. **Install Dependencies**:
```bash
pip install -r require.txt
```

2. **Run the Application**:
```bash
python  main.py
```

The API will be available at `http://localhost:5000/'


## 🔍 Data Extraction Details

### Product Catalog
- Uses Shopify's `/products.json` endpoint
- Handles pagination automatically
- Extracts: ID, title, price, images, availability, vendor info

### Hero Products
- Scrapes homepage for featured products
- Identifies product links in hero sections
- Extracts product details for each hero item

### Policies
- Common URL patterns: `/pages/privacy-policy`, `/policies/privacy-policy`
- Extracts both URL and content
- Handles various policy page structures

### FAQs
- Multiple extraction strategies for different FAQ formats
- Supports structured FAQs and plain text Q&A
- Regex patterns for question-answer detection

### Contact Information
- Email extraction using regex patterns
- Phone number detection with international formats
- Address extraction from structured data

### Social Media
- Pattern matching for all major platforms
- Extracts handles from links and text content
- Supports Instagram, Facebook, TikTok, Twitter, etc.

## 📊 Performance

- **Async Processing**: Concurrent extraction of different data types
- **Request Optimization**: Smart request batching and caching
- **Error Recovery**: Graceful handling of failed requests
- **Resource Management**: Memory-efficient data processing

## 🛡️ Security & Best Practices

- Input validation using Pydantic models
- Proper error handling without exposing internals
- Request timeout protection
- Rate limiting considerations
- User-agent rotation capability

## 🤝 Contributing

1. Follow PEP 8 coding standards
2. Add type hints for all functions
3. Include comprehensive docstrings
4. Write tests for new features
5. Update documentation


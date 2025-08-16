// Modern JavaScript for Shopify Store Scraper

document.addEventListener('DOMContentLoaded', function() {
    initializeFormHandlers();
    initializeAPITester();
    initializeAnalysisOptions();
    initializeAnimations();
});

// Analysis options handling
function initializeAnalysisOptions() {
    const optionCards = document.querySelectorAll('.option-card');
    const includeCompetitorsInput = document.getElementById('include_competitors');
    
    // Set basic analysis as default
    const basicCard = document.querySelector('[data-option="basic"]');
    if (basicCard) {
        basicCard.classList.add('active');
    }
    
    optionCards.forEach(card => {
        card.addEventListener('click', function() {
            // Remove active class from all cards
            optionCards.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked card
            this.classList.add('active');
            
            // Update hidden input based on selection
            const option = this.dataset.option;
            if (includeCompetitorsInput) {
                includeCompetitorsInput.value = option === 'advanced' ? 'true' : 'false';
            }
            
            // Update form action based on selection
            const form = document.getElementById('scrapeForm');
            if (form && option === 'advanced') {
                // For advanced analysis, we'll handle this differently
                form.dataset.analysisType = 'advanced';
            } else {
                form.dataset.analysisType = 'basic';
            }
            
            // Visual feedback
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
}

// Enhanced form handlers
function initializeFormHandlers() {
    const scrapeForm = document.getElementById('scrapeForm');
    const scrapeBtn = document.getElementById('scrapeBtn');
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    
    if (scrapeForm) {
        scrapeForm.addEventListener('submit', function(e) {
            const analysisType = this.dataset.analysisType || 'basic';
            const websiteUrl = document.getElementById('website_url').value;
            
            if (analysisType === 'advanced') {
                // For advanced analysis, use API endpoint with competitors
                e.preventDefault();
                handleAdvancedAnalysis(websiteUrl, scrapeBtn, loadingModal);
            } else {
                // Show loading modal for basic analysis
                showLoadingModal(loadingModal, scrapeBtn, 'basic');
            }
        });
    }
}

// Handle advanced analysis with competitors
async function handleAdvancedAnalysis(websiteUrl, scrapeBtn, loadingModal) {
    if (!websiteUrl) {
        showAlert('Please enter a website URL', 'danger');
        return;
    }
    
    // Add protocol if missing
    if (!websiteUrl.startsWith('http://') && !websiteUrl.startsWith('https://')) {
        websiteUrl = 'https://' + websiteUrl;
    }
    
    showLoadingModal(loadingModal, scrapeBtn, 'advanced');
    
    try {
        const response = await axios.post('/api/scrape-with-competitors', {
            website_url: websiteUrl,
            include_competitors: true
        }, {
            timeout: 300000, // 5 minutes timeout for competitor analysis
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // Hide loading modal
        loadingModal.hide();
        resetButton(scrapeBtn);
        
        // Show success message
        showAlert('Analysis completed successfully! Competitor analysis is running in background.', 'success');
        
        // Redirect to results or show data
        if (response.data.brand_id) {
            window.location.href = `/api/brands/${response.data.brand_id}`;
        }
        
    } catch (error) {
        loadingModal.hide();
        resetButton(scrapeBtn);
        
        let errorMessage = 'Analysis failed. Please try again.';
        if (error.response && error.response.data && error.response.data.message) {
            errorMessage = error.response.data.message;
        }
        
        showAlert(errorMessage, 'danger');
        console.error('Advanced analysis error:', error);
    }
}

// Show loading modal with dynamic content
function showLoadingModal(loadingModal, button, type) {
    const loadingTitle = document.getElementById('loadingTitle');
    const loadingSubtitle = document.getElementById('loadingSubtitle');
    
    if (type === 'advanced') {
        loadingTitle.textContent = 'Analyzing Store & Competitors...';
        loadingSubtitle.textContent = 'AI-powered competitor discovery and comprehensive analysis';
        
        // Update button
        button.disabled = true;
        button.innerHTML = '<span class="btn-content"><i class="fas fa-users me-2"></i><span class="btn-text">Analyzing with AI...</span></span>';
    } else {
        loadingTitle.textContent = 'Analyzing Store Data...';
        loadingSubtitle.textContent = 'Extracting comprehensive insights and intelligence';
        
        // Update button
        button.disabled = true;
        button.innerHTML = '<span class="btn-content"><i class="fas fa-spinner fa-spin me-2"></i><span class="btn-text">Processing...</span></span>';
    }
    
    loadingModal.show();
    
    // Animate progress bar
    const progressBar = document.getElementById('progressBar');
    if (progressBar) {
        progressBar.style.width = '0%';
        setTimeout(() => {
            progressBar.style.width = '100%';
        }, 100);
    }
}

// Reset button to original state
function resetButton(button) {
    button.disabled = false;
    button.innerHTML = '<span class="btn-content"><i class="fas fa-rocket me-2"></i><span class="btn-text">Launch Analysis</span></span><div class="btn-shine"></div>';
}

// Show alert message
function showAlert(message, type) {
    const alertContainer = document.querySelector('.card-body-modern');
    const alertElement = document.createElement('div');
    alertElement.className = `alert-modern alert-${type}`;
    alertElement.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close-modern float-end" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    if (alertContainer) {
        alertContainer.insertBefore(alertElement, alertContainer.firstChild);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alertElement.parentElement) {
                alertElement.remove();
            }
        }, 5000);
    }
}

// Enhanced API testing
function initializeAPITester() {
    const apiTestBtn = document.getElementById('apiTestBtn');
    const apiTestSection = document.getElementById('apiTestSection');
    const sendApiRequest = document.getElementById('sendApiRequest');
    const sendCompetitorRequest = document.getElementById('sendCompetitorRequest');

    if (apiTestBtn && apiTestSection) {
        apiTestBtn.addEventListener('click', function() {
            const isVisible = apiTestSection.style.display !== 'none';
            
            if (isVisible) {
                apiTestSection.style.display = 'none';
                this.innerHTML = '<span class="btn-content"><i class="fas fa-code me-2"></i><span class="btn-text">API Testing</span></span>';
                apiTestSection.style.animation = 'fadeOut 0.3s ease-out';
            } else {
                apiTestSection.style.display = 'block';
                this.innerHTML = '<span class="btn-content"><i class="fas fa-times me-2"></i><span class="btn-text">Hide API Test</span></span>';
                apiTestSection.style.animation = 'fadeInUp 0.5s ease-out';
            }
        });
    }

    if (sendApiRequest) {
        sendApiRequest.addEventListener('click', () => sendAPIRequest(false));
    }

    if (sendCompetitorRequest) {
        sendCompetitorRequest.addEventListener('click', () => sendAPIRequest(true));
    }
}

// Enhanced API request function
async function sendAPIRequest(includeCompetitors = false) {
    const apiUrl = document.getElementById('apiUrl').value.trim();
    const apiResponse = document.getElementById('apiResponse');
    const sendBtn = includeCompetitors ? document.getElementById('sendCompetitorRequest') : document.getElementById('sendApiRequest');
    
    if (!apiUrl) {
        showApiResponse('<span class="text-danger">Please enter a URL</span>', apiResponse);
        return;
    }
    
    // Validate URL format
    try {
        new URL(apiUrl.startsWith('http') ? apiUrl : `https://${apiUrl}`);
    } catch (e) {
        showApiResponse('<span class="text-danger">Invalid URL format</span>', apiResponse);
        return;
    }
    
    // Show loading state
    const originalContent = sendBtn.innerHTML;
    sendBtn.disabled = true;
    sendBtn.innerHTML = includeCompetitors ? 
        '<i class="fas fa-spinner fa-spin me-2"></i>Analyzing with Competitors...' :
        '<i class="fas fa-spinner fa-spin me-2"></i>Analyzing Store...';
    
    showApiResponse('<div class="loading-api"><i class="fas fa-spinner fa-spin me-2"></i>Processing request...</div>', apiResponse);
    
    try {
        const endpoint = includeCompetitors ? '/api/scrape-with-competitors' : '/api/scrape';
        const requestData = {
            website_url: apiUrl.startsWith('http') ? apiUrl : `https://${apiUrl}`
        };
        
        if (includeCompetitors) {
            requestData.include_competitors = true;
        }
        
        const response = await axios.post(endpoint, requestData, {
            timeout: includeCompetitors ? 300000 : 120000, // 5 min for competitors, 2 min for basic
            headers: { 'Content-Type': 'application/json' }
        });
        
        // Display successful response
        const responseHtml = `
            <div class="response-success mb-3">
                <div class="response-status">
                    <i class="fas fa-check-circle text-success me-2"></i>
                    <strong>Status:</strong> ${response.status} ${response.statusText}
                </div>
                ${response.data.brand_id ? `
                    <div class="response-info mt-2">
                        <i class="fas fa-database text-info me-2"></i>
                        <strong>Brand ID:</strong> ${response.data.brand_id}
                    </div>
                ` : ''}
                ${response.data.competitor_analysis ? `
                    <div class="response-competitor mt-2">
                        <i class="fas fa-users text-warning me-2"></i>
                        <strong>Competitor Analysis:</strong> ${response.data.competitor_analysis.status}
                    </div>
                ` : ''}
            </div>
            <details class="response-details">
                <summary>View Full Response</summary>
                <pre class="response-json">${JSON.stringify(response.data, null, 2)}</pre>
            </details>
        `;
        
        showApiResponse(responseHtml, apiResponse);
        
    } catch (error) {
        let errorHtml = '';
        
        if (error.response) {
            errorHtml = `
                <div class="response-error mb-3">
                    <div class="error-status">
                        <i class="fas fa-exclamation-triangle text-danger me-2"></i>
                        <strong>Error:</strong> ${error.response.status} - ${error.response.data?.message || 'Server error'}
                    </div>
                </div>
                <details class="response-details">
                    <summary>View Error Details</summary>
                    <pre class="response-json">${JSON.stringify(error.response.data, null, 2)}</pre>
                </details>
            `;
        } else if (error.request) {
            errorHtml = `
                <div class="response-error">
                    <i class="fas fa-wifi text-danger me-2"></i>
                    <strong>Network Error:</strong> No response from server
                </div>
            `;
        } else {
            errorHtml = `
                <div class="response-error">
                    <i class="fas fa-exclamation text-danger me-2"></i>
                    <strong>Request Error:</strong> ${error.message}
                </div>
            `;
        }
        
        showApiResponse(errorHtml, apiResponse);
        console.error('API Error:', error);
    } finally {
        // Reset button state
        sendBtn.disabled = false;
        sendBtn.innerHTML = originalContent;
    }
}

// Show API response with enhanced styling
function showApiResponse(content, container) {
    container.innerHTML = content;
    container.scrollTop = 0;
}

// Initialize animations and interactions
function initializeAnimations() {
    // Add intersection observer for animations
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animationPlayState = 'running';
            }
        });
    }, observerOptions);
    
    // Observe elements with animations
    document.querySelectorAll('.feature-card').forEach(card => {
        card.style.animationPlayState = 'paused';
        observer.observe(card);
    });
    
    // Add hover effects to buttons
    document.querySelectorAll('.btn-modern').forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        btn.addEventListener('mouseleave', function() {
            if (!this.disabled) {
                this.style.transform = '';
            }
        });
    });
    
    // Enhanced input focus effects
    document.querySelectorAll('.form-control-modern').forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.style.transform = 'scale(1.02)';
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.style.transform = '';
        });
    });
}

// Utility functions
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text);
    } else {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        return new Promise((resolve, reject) => {
            document.execCommand('copy') ? resolve() : reject();
            textArea.remove();
        });
    }
}

// Enhanced error handling for images
document.addEventListener('error', function(e) {
    if (e.target.tagName === 'IMG') {
        e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMjIyIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzY2NyIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlIG5vdCBmb3VuZDwvdGV4dD48L3N2Zz4=';
        e.target.alt = 'Image not available';
    }
}, true);

// Smooth scrolling for anchor links
document.addEventListener('click', function(e) {
    if (e.target.tagName === 'A' && e.target.getAttribute('href')?.startsWith('#')) {
        e.preventDefault();
        const targetId = e.target.getAttribute('href').substring(1);
        const targetElement = document.getElementById(targetId);
        
        if (targetElement) {
            targetElement.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    }
});

// Add CSS for additional styles
const additionalStyles = `
<style>
.loading-api {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    color: var(--text-secondary);
}

.response-success, .response-error {
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
}

.response-success {
    background: rgba(79, 172, 254, 0.1);
    border-left: 4px solid #00f2fe;
}

.response-error {
    background: rgba(245, 87, 108, 0.1);
    border-left: 4px solid #f5576c;
}

.response-details summary {
    cursor: pointer;
    padding: 0.5rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
    margin-bottom: 0.5rem;
}

.response-json {
    background: rgba(0, 0, 0, 0.3);
    padding: 1rem;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    overflow-x: auto;
    white-space: pre-wrap;
    color: var(--text-secondary);
}

@keyframes fadeOut {
    from { opacity: 1; transform: translateY(0); }
    to { opacity: 0; transform: translateY(-20px); }
}

.btn-close-modern {
    background: none;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    padding: 0.25rem;
}

.btn-close-modern:hover {
    color: var(--text-primary);
}
</style>
`;

// Inject additional styles
document.head.insertAdjacentHTML('beforeend', additionalStyles);
// Main JavaScript file for Shopify Store Scraper

document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initializeFormHandlers();
    initializeAPITester();
    initializeTooltips();
});

function initializeFormHandlers() {
    const scrapeForm = document.getElementById('scrapeForm');
    const scrapeBtn = document.getElementById('scrapeBtn');
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));

    if (scrapeForm) {
        scrapeForm.addEventListener('submit', function(e) {
            // Show loading modal
            loadingModal.show();
            
            // Add loading state to button
            if (scrapeBtn) {
                scrapeBtn.disabled = true;
                scrapeBtn.innerHTML = '<span class="loading-spinner me-2"></span>Scraping...';
            }
        });
    }
}

function initializeAPITester() {
    const apiTestBtn = document.getElementById('apiTestBtn');
    const apiTestSection = document.getElementById('apiTestSection');
    const sendApiRequest = document.getElementById('sendApiRequest');

    if (apiTestBtn && apiTestSection) {
        apiTestBtn.addEventListener('click', function() {
            const isVisible = apiTestSection.style.display !== 'none';
            apiTestSection.style.display = isVisible ? 'none' : 'block';
            
            // Update button text
            apiTestBtn.innerHTML = isVisible 
                ? '<i class="fas fa-code me-2"></i>Test API'
                : '<i class="fas fa-times me-2"></i>Hide API Test';
        });
    }

    if (sendApiRequest) {
        sendApiRequest.addEventListener('click', function() {
            sendAPIRequest();
        });
    }
}

function initializeTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

async function sendAPIRequest() {
    const apiUrl = document.getElementById('apiUrl').value.trim();
    const apiResponse = document.getElementById('apiResponse');
    const sendBtn = document.getElementById('sendApiRequest');
    
    if (!apiUrl) {
        apiResponse.innerHTML = '<span class="text-danger">Please enter a URL</span>';
        return;
    }
    
    // Validate URL format
    try {
        new URL(apiUrl.startsWith('http') ? apiUrl : `https://${apiUrl}`);
    } catch (e) {
        apiResponse.innerHTML = '<span class="text-danger">Invalid URL format</span>';
        return;
    }
    
    // Show loading state
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<span class="loading-spinner me-2"></span>Sending...';
    apiResponse.innerHTML = '<span class="text-info">Sending API request...</span>';
    
    try {
        const response = await axios.post('/api/scrape', {
            website_url: apiUrl.startsWith('http') ? apiUrl : `https://${apiUrl}`
        }, {
            timeout: 120000, // 2 minutes timeout
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // Display successful response
        apiResponse.innerHTML = `
            <div class="text-success mb-2">
                <strong>Status:</strong> ${response.status} ${response.statusText}
            </div>
            <pre class="text-light">${JSON.stringify(response.data, null, 2)}</pre>
        `;
        
    } catch (error) {
        let errorMessage = 'Unknown error occurred';
        let statusCode = 'N/A';
        
        if (error.response) {
            // Server responded with error status
            statusCode = error.response.status;
            errorMessage = error.response.data?.message || error.response.statusText || 'Server error';
            
            apiResponse.innerHTML = `
                <div class="text-danger mb-2">
                    <strong>Error:</strong> ${statusCode} - ${errorMessage}
                </div>
                <pre class="text-light">${JSON.stringify(error.response.data, null, 2)}</pre>
            `;
        } else if (error.request) {
            // Request was made but no response received
            errorMessage = 'No response from server (timeout or network error)';
            apiResponse.innerHTML = `
                <div class="text-danger">
                    <strong>Network Error:</strong> ${errorMessage}
                </div>
            `;
        } else {
            // Something else happened
            errorMessage = error.message || 'Request setup error';
            apiResponse.innerHTML = `
                <div class="text-danger">
                    <strong>Request Error:</strong> ${errorMessage}
                </div>
            `;
        }
        
        console.error('API Error:', error);
    } finally {
        // Reset button state
        sendBtn.disabled = false;
        sendBtn.innerHTML = '<i class="fas fa-paper-plane me-2"></i>Send API Request';
    }
}

// Utility functions
function formatFileSize(bytes) {
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
        // Fallback for older browsers
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

// Add copy functionality to code blocks
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('copy-btn')) {
        const codeBlock = e.target.nextElementSibling;
        const text = codeBlock.textContent;
        
        copyToClipboard(text).then(() => {
            e.target.innerHTML = '<i class="fas fa-check me-1"></i>Copied!';
            setTimeout(() => {
                e.target.innerHTML = '<i class="fas fa-copy me-1"></i>Copy';
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy:', err);
        });
    }
});

// Auto-resize textarea elements
function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

// Add auto-resize to all textareas
document.addEventListener('input', function(e) {
    if (e.target.tagName.toLowerCase() === 'textarea') {
        autoResizeTextarea(e.target);
    }
});

// Initialize auto-resize for existing textareas
document.addEventListener('DOMContentLoaded', function() {
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(autoResizeTextarea);
});

// Handle form validation
function validateUrl(url) {
    try {
        const urlObj = new URL(url.startsWith('http') ? url : `https://${url}`);
        return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
    } catch (e) {
        return false;
    }
}

// Add real-time URL validation
document.addEventListener('input', function(e) {
    if (e.target.type === 'url') {
        const isValid = validateUrl(e.target.value);
        e.target.classList.toggle('is-valid', isValid && e.target.value.length > 0);
        e.target.classList.toggle('is-invalid', !isValid && e.target.value.length > 0);
    }
});

// Error handling for images
document.addEventListener('error', function(e) {
    if (e.target.tagName === 'IMG') {
        e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlIG5vdCBmb3VuZDwvdGV4dD48L3N2Zz4=';
        e.target.alt = 'Image not available';
    }
}, true);

// Add smooth scrolling to anchor links
document.addEventListener('click', function(e) {
    if (e.target.tagName === 'A' && e.target.getAttribute('href').startsWith('#')) {
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

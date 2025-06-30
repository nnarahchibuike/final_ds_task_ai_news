// Configuration - Use relative URLs since frontend is served from same server
const API_BASE_URL = '';

// Global state
let currentArticles = [];

// DOM elements
const loadingEl = document.getElementById('loading');
const errorEl = document.getElementById('error');
const mainContentEl = document.getElementById('main-content');
const newsGridEl = document.getElementById('news-grid');
const articleCountEl = document.getElementById('article-count');
const lastUpdatedEl = document.getElementById('last-updated');
const errorMessageEl = document.getElementById('error-message');

// Modal elements
const modalEl = document.getElementById('recommendations-modal');
const modalOverlayEl = document.getElementById('modal-overlay');
const recommendationsLoadingEl = document.getElementById('recommendations-loading');
const recommendationsContentEl = document.getElementById('recommendations-content');
const recommendationsErrorEl = document.getElementById('recommendations-error');

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    console.log('AI News Hub initialized');
    fetchNews();
});

// Fetch news from API
async function fetchNews() {
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE_URL}/fetch-news`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success' && data.articles) {
            currentArticles = data.articles;
            displayNews(data.articles);
            updateStats(data.total_articles, data.last_processed);
            showMainContent();
        } else {
            throw new Error(data.message || 'No articles available');
        }
        
    } catch (error) {
        console.error('Error fetching news:', error);
        showError(error.message);
    }
}

// Display news articles
function displayNews(articles) {
    newsGridEl.innerHTML = '';
    
    articles.forEach(article => {
        const articleCard = createArticleCard(article);
        newsGridEl.appendChild(articleCard);
    });
}

// Create individual article card
function createArticleCard(article) {
    const card = document.createElement('div');
    card.className = 'news-card';
    
    // Format date
    const date = formatDate(article.date);
    
    // Get up to 3 tags
    const tags = article.tags ? article.tags.slice(0, 3) : [];
    
    // Extract source name from URL
    const sourceName = extractSourceName(article.source);
    
    card.innerHTML = `
        <div class="news-header">
            <h2 class="news-title">
                <a href="${article.url}" target="_blank" rel="noopener noreferrer">
                    ${escapeHtml(article.title)}
                </a>
            </h2>
            <div class="news-meta">
                <span class="news-source">${escapeHtml(sourceName)}</span>
                <span class="news-date">${date}</span>
            </div>
        </div>
        
        <div class="news-summary">
            ${escapeHtml(article.summary || 'No summary available.')}
        </div>
        
        ${tags.length > 0 ? `
            <div class="news-tags">
                ${tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
            </div>
        ` : ''}
        
        <div class="news-actions">
            <button class="related-btn" onclick="showRecommendations('${article.id}')">
                <i class="fas fa-lightbulb"></i>
                Related Topics
            </button>
            <a href="${article.url}" target="_blank" rel="noopener noreferrer" class="read-more">
                Read More
                <i class="fas fa-external-link-alt"></i>
            </a>
        </div>
    `;
    
    return card;
}

// Show recommendations modal
async function showRecommendations(articleId) {
    try {
        // Show modal and loading state
        modalEl.classList.remove('hidden');
        modalOverlayEl.classList.remove('hidden');
        recommendationsLoadingEl.classList.remove('hidden');
        recommendationsContentEl.classList.add('hidden');
        recommendationsErrorEl.classList.add('hidden');
        
        // Fetch recommendations
        const response = await fetch(`${API_BASE_URL}/recommend-news?article_id=${encodeURIComponent(articleId)}&max_results=5`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.articles && data.articles.length > 0) {
            displayRecommendations(data.articles);
        } else {
            throw new Error('No related articles found');
        }
        
    } catch (error) {
        console.error('Error fetching recommendations:', error);
        showRecommendationsError();
    }
}

// Display recommendations in modal
function displayRecommendations(recommendations) {
    recommendationsLoadingEl.classList.add('hidden');
    recommendationsErrorEl.classList.add('hidden');
    
    recommendationsContentEl.innerHTML = '';
    
    recommendations.forEach(article => {
        const item = document.createElement('div');
        item.className = 'recommendation-item';
        
        const date = formatDate(article.date);
        const sourceName = extractSourceName(article.source);

        // Get up to 3 tags for recommendations
        const tags = article.tags ? article.tags.slice(0, 3) : [];

        item.innerHTML = `
            <div class="recommendation-title">
                <a href="${article.url}" target="_blank" rel="noopener noreferrer">
                    ${escapeHtml(article.title)}
                </a>
            </div>
            <div class="recommendation-summary">
                ${escapeHtml(article.summary || 'No summary available.')}
            </div>
            ${tags.length > 0 ? `
                <div class="news-tags" style="margin-top: 8px;">
                    ${tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
                </div>
            ` : ''}
            <div class="news-meta" style="margin-top: 8px;">
                <span class="news-source">${escapeHtml(sourceName)}</span>
                <span class="news-date">${date}</span>
            </div>
        `;
        
        recommendationsContentEl.appendChild(item);
    });
    
    recommendationsContentEl.classList.remove('hidden');
}

// Show recommendations error
function showRecommendationsError() {
    recommendationsLoadingEl.classList.add('hidden');
    recommendationsContentEl.classList.add('hidden');
    recommendationsErrorEl.classList.remove('hidden');
}

// Close recommendations modal
function closeRecommendations() {
    modalEl.classList.add('hidden');
    modalOverlayEl.classList.add('hidden');
}

// Update header stats
function updateStats(totalArticles, lastProcessed) {
    articleCountEl.textContent = `${totalArticles} articles`;
    
    if (lastProcessed) {
        const date = new Date(lastProcessed);
        lastUpdatedEl.textContent = `Last updated: ${date.toLocaleString()}`;
    }
}

// Show loading state
function showLoading() {
    loadingEl.classList.remove('hidden');
    errorEl.classList.add('hidden');
    mainContentEl.classList.add('hidden');
}

// Show error state
function showError(message) {
    loadingEl.classList.add('hidden');
    mainContentEl.classList.add('hidden');
    errorMessageEl.textContent = message;
    errorEl.classList.remove('hidden');
}

// Show main content
function showMainContent() {
    loadingEl.classList.add('hidden');
    errorEl.classList.add('hidden');
    mainContentEl.classList.remove('hidden');
}

// Utility functions
function formatDate(dateString) {
    if (!dateString) return 'Unknown date';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch (error) {
        return 'Invalid date';
    }
}

function extractSourceName(sourceUrl) {
    if (!sourceUrl) return 'Unknown Source';

    // If it's already a clean source name (not a URL), return it
    if (!sourceUrl.includes('http') && !sourceUrl.includes('/')) {
        return sourceUrl.charAt(0).toUpperCase() + sourceUrl.slice(1);
    }

    try {
        const url = new URL(sourceUrl);
        return url.hostname.replace('www.', '').replace('.com', '').replace('.org', '').replace('.net', '');
    } catch (error) {
        // If URL parsing fails, try to extract from string
        return sourceUrl.split('/').pop().replace('.xml', '').replace('.rss', '') || 'Unknown Source';
    }
}

function escapeHtml(text) {
    if (!text) return '';
    
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modal when clicking outside
modalOverlayEl.addEventListener('click', closeRecommendations);

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && !modalEl.classList.contains('hidden')) {
        closeRecommendations();
    }
});

// Auto-refresh every 30 minutes
setInterval(fetchNews, 30 * 60 * 1000);

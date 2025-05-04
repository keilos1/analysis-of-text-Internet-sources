document.addEventListener("DOMContentLoaded", function() {
    setCurrentDate();
    setupNavigation();
    loadPage(getCurrentPage());
    
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-article]')) {
            e.preventDefault();
            const articleId = e.target.getAttribute('data-article');
            loadArticle(articleId);
        }
        
        if (e.target.matches('.search-item-title') && e.target.href) {
            return;
        }
    });

    initSearch();
});

function initSearch() {
    const searchInput = document.querySelector('.search-input');
    const searchButton = document.querySelector('.search-button');
    
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = this.value.trim();
                if (query) performSearch(query);
            }
        });
    }
    
    if (searchButton) {
        searchButton.addEventListener('click', function() {
            const query = searchInput.value.trim();
            if (query) performSearch(query);
        });
    }
}

function setCurrentDate() {
    const dateElement = document.getElementById("current-date");
    if (!dateElement) return;

    const today = new Date();
    const options = { weekday: 'short', day: 'numeric', month: 'long', year: 'numeric' };
    dateElement.textContent = today.toLocaleDateString('ru-RU', options);
}

function setupNavigation() {
    document.querySelectorAll('[data-page]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.getAttribute('data-page');
            const type = this.getAttribute('data-type');
            
            const url = type ? `?page=${page}&type=${type}` : `?page=${page}`;
            history.pushState({ page, type }, '', url);
            loadPage({ page, type });
        });
    });
    
    window.addEventListener('popstate', function(e) {
        loadPage(e.state || getCurrentPage());
    });
}

function getCurrentPage() {
    const params = new URLSearchParams(window.location.search);
    return {
        page: params.get('page') || 'main',
        type: params.get('type') || null,
        query: params.get('query') || null
    };
}

async function loadPage(params) {
    const { page, type, query } = params;
    const contentContainer = document.getElementById('dynamic-content') || document.body;
    
    try {
        switch(page) {
            case 'main':
                await loadMainPage(contentContainer);
                break;
            case 'category':
                await loadCategoryPage(contentContainer, type);
                break;
            case 'source':
                await loadSourcePage(contentContainer, type);
                break;
            case 'article':
                await loadArticlePage(contentContainer, type);
                break;
            case 'search':
                await loadSearchResultsPage(contentContainer, query);
                break;
            default:
                await loadMainPage(contentContainer);
        }
    } catch (error) {
        console.error('Page load error:', error);
        contentContainer.innerHTML = `
            <div class="error">
                <h2>Ошибка загрузки</h2>
                <p>${error.message}</p>
            </div>
        `;
    }
}

async function fetchArticles(limit = 5, category = null, source = null) {
    let url = `/api/articles?limit=${limit}`;
    if (category) url += `&category=${encodeURIComponent(category)}`;
    if (source) url += `&source=${encodeURIComponent(source)}`;
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('Ошибка загрузки статей');
    return await response.json();
}

async function loadMainPage(container) {
    container.innerHTML = '<div class="loading">Загрузка новостей...</div>';
    const articles = await fetchArticles(5);
    renderArticles(container, articles, 'Последние новости');
}

async function loadCategoryPage(container, category) {
    container.innerHTML = '<div class="loading">Загрузка новостей...</div>';
    const articles = await fetchArticles(10, category);
    renderArticles(container, articles, `Категория: ${category}`);
}

async function loadSourcePage(container, source) {
    container.innerHTML = '<div class="loading">Загрузка новостей...</div>';
    const articles = await fetchArticles(10, null, source);
    renderArticles(container, articles, `Источник: ${source}`);
}

function renderArticles(container, articles, title) {
    if (!articles.length) {
        container.innerHTML = '<div class="no-articles">Новости не найдены</div>';
        return;
    }

    let html = `
        <section class="news-section">
            <h2>${title}</h2>
            <div class="news-list">
    `;

    articles.forEach(article => {
        html += `
            <div class="news-item">
                <img src="/foto.jpg" alt="${article.title}">
                <div class="news-content">
                    <h3><a href="#" data-article="${article._id}">${article.title}</a></h3>
                    <p>${article.summary || ''}</p>
                    <div class="news-meta">
                        <span>${article.category || ''}</span>
                        <span>${formatDate(article.publication_date)}</span>
                    </div>
                </div>
            </div>
        `;
    });

    html += `</div></section>`;
    container.innerHTML = html;
}

async function loadArticle(articleId) {
    const contentContainer = document.getElementById('dynamic-content');
    contentContainer.innerHTML = '<div class="loading">Загрузка статьи...</div>';
    
    try {
        const response = await fetch(`/api/articles/${articleId}`);
        if (!response.ok) throw new Error('Статья не найдена');
        const article = await response.json();
        
        history.pushState({ page: 'article', type: articleId }, '', `?page=article&id=${articleId}`);
        
        contentContainer.innerHTML = `
            <article class="full-article">
                <h1>${article.title}</h1>
                <div class="article-meta">
                    <span>${article.category || ''}</span>
                    <span>${formatDate(article.publication_date)}</span>
                    <span>${article.source || ''}</span>
                    ${article.area_of_the_city ? `<span>${article.area_of_the_city}</span>` : ''}
                </div>
                <img src="/foto.jpg" alt="${article.title}">
                <div class="article-content">${article.text || article.summary || ''}</div>
            </article>
        `;
    } catch (error) {
        contentContainer.innerHTML = `
            <div class="error">
                <h2>Ошибка загрузки статьи</h2>
                <p>${error.message}</p>
            </div>
        `;
    }
}

function loadArticlePage(container, articleId) {
    loadArticle(articleId);
}

async function performSearch(query) {
    const contentContainer = document.getElementById('dynamic-content');
    contentContainer.innerHTML = '<div class="loading">Поиск новостей...</div>';
    
    try {
        const response = await fetch(`/api/search?query=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error('Ошибка поиска');
        const results = await response.json();
        
        sessionStorage.setItem('searchResults', JSON.stringify({ query, results }));
        history.pushState({ page: 'search', query }, '', `?page=search&query=${encodeURIComponent(query)}`);
        loadSearchResultsPage(contentContainer, query);
    } catch (error) {
        contentContainer.innerHTML = `
            <div class="error">
                <h2>Ошибка поиска</h2>
                <p>${error.message}</p>
            </div>
        `;
    }
}

function loadSearchResultsPage(container, query) {
    const savedData = sessionStorage.getItem('searchResults');
    const searchData = savedData ? JSON.parse(savedData) : { query, results: [] };
    
    let html = `
        <div class="search-results">
            <h2>Результаты поиска: "${searchData.query}"</h2>
            <div class="results-count">Найдено: ${searchData.results.length}</div>
    `;

    if (searchData.results.length) {
        html += '<div class="results-list">';
        searchData.results.forEach(item => {
            html += `
                <div class="result-item">
                    <h3><a href="#" data-article="${item._id}">${item.title}</a></h3>
                    <p>${item.summary || ''}</p>
                    <div class="result-meta">
                        <span>${item.category || ''}</span>
                        <span>${formatDate(item.publication_date)}</span>
                    </div>
                </div>
            `;
        });
        html += '</div>';
    } else {
        html += '<div class="no-results">Ничего не найдено</div>';
    }

    html += '</div>';
    container.innerHTML = html;
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU');
}

document.addEventListener("DOMContentLoaded", function() {
    // Установка текущей даты
    setCurrentDate();
    
    // Обработка навигации
    setupNavigation();
    
    // Загрузка начальной страницы
    loadPage(getCurrentPage());
    
    // Обработка кликов по статьям
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-article]')) {
            e.preventDefault();
            const articleId = e.target.getAttribute('data-article');
            loadArticle(articleId);
        }
        
        // Обработка кликов по внешним ссылкам в результатах поиска
        if (e.target.matches('.search-item-title') && e.target.href) {
            // Открываем в новой вкладке, переход обрабатывается естественным образом
            return;
        }
    });

    // Инициализация поиска
    initSearch();
});

// ========== API Functions ==========
async function fetchArticles(limit = 5, category = null, source = null) {
    try {
        let url = 'http://localhost:8000/api/articles';
        const params = new URLSearchParams();
        
        if (limit) params.append('limit', limit);
        if (category) params.append('category', category);
        if (source) params.append('source', source);
        
        if (params.toString()) url += `?${params.toString()}`;
        
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching articles:', error);
        return [];
    }
}

async function fetchArticleById(id) {
    try {
        const response = await fetch(`http://localhost:8000/api/articles/${id}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching article:', error);
        return null;
    }
}

async function searchArticles(query) {
    try {
        const response = await fetch(`http://localhost:8000/api/search?query=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Error searching articles:', error);
        return [];
    }
}

// ========== Utility Functions ==========
function setCurrentDate() {
    const dateElement = document.getElementById("current-date");
    if (!dateElement) return;

    const today = new Date();
    const weekdayShort = today.toLocaleDateString("ru-RU", { weekday: 'short' });
    const weekdayFormatted = weekdayShort.charAt(0).toUpperCase() + weekdayShort.slice(1).toLowerCase();
    const day = today.getDate();
    const month = today.toLocaleDateString("ru-RU", { month: 'long' });
    const year = today.getFullYear();

    dateElement.innerHTML = `
        <div class="date-weekday">${weekdayFormatted}</div>
        <div class="date-day">${day}</div>
        <div class="date-month">${month}</div>
        <div class="date-year">${year}</div>
    `;
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
        if (e.state) {
            loadPage(e.state);
        } else {
            loadPage(getCurrentPage());
        }
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

// ========== Page Loading Functions ==========
async function loadPage(params) {
    const { page, type, query } = params;
    const contentContainer = document.getElementById('dynamic-content');
    
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
}

async function loadMainPage(container) {
    container.innerHTML = '<div class="loading-spinner">Загрузка новостей...</div>';
    
    try {
        const articles = await fetchArticles(5);
        
        let digestHTML = `
            <section class="digest">
                <h2>Новости дня</h2>
                <ul>
        `;
        
        articles.slice(0, 3).forEach(article => {
            digestHTML += `<li><a href="#" data-article="${article._id}">${article.title}</a></li>`;
        });
        
        digestHTML += `
                </ul>
            </section>
            <section class="latest-news">
                <h2>Последние новости</h2>
        `;
        
        articles.forEach(article => {
            digestHTML += `
                <div class="news-item">
                    <img src="${article.image || 'foto.jpg'}" alt="${article.title}">
                    <div class="news-text">
                        <a href="#" data-article="${article._id}" class="news-title">${article.title}</a>
                        <p>${article.summary || 'Описание новости отсутствует'}</p>
                    </div>
                </div>
            `;
        });
        
        digestHTML += `</section>`;
        container.innerHTML = digestHTML;
    } catch (error) {
        container.innerHTML = `
            <div class="error-message">
                <p>Не удалось загрузить новости. Пожалуйста, попробуйте позже.</p>
                <button onclick="location.reload()">Обновить страницу</button>
            </div>
        `;
    }
}

async function loadCategoryPage(container, category) {
    const categoryNames = {
        "culture": "Культура",
        "sports": "Спорт",
        "tech": "Технологии",
        "holidays": "Праздники",
        "education": "Образование"
    };
    
    container.innerHTML = '<div class="loading-spinner">Загрузка новостей...</div>';
    
    try {
        const articles = await fetchArticles(10, category);
        const categoryName = categoryNames[category] || "Категория";

        let digestHTML = `
            <section class="digest">
                <h2>Новости дня</h2>
                <ul>
        `;

        articles.slice(0, 3).forEach(article => {
            digestHTML += `<li><a href="#" data-article="${article._id}">${article.title}</a></li>`;
        });

        digestHTML += `
                </ul>
            </section>
            <section class="latest-news">
                <h2>Новости: ${categoryName}</h2>
        `;

        articles.forEach(article => {
            digestHTML += `
                <div class="news-item">
                    <img src="${article.image || 'foto.jpg'}" alt="${article.title}">
                    <div class="news-text">
                        <a href="#" data-article="${article._id}" class="news-title">${article.title}</a>
                        <p>${article.summary || 'Описание новости отсутствует'}</p>
                    </div>
                </div>
            `;
        });

        digestHTML += `</section>`;
        container.innerHTML = digestHTML;
    } catch (error) {
        container.innerHTML = `
            <div class="error-message">
                <p>Не удалось загрузить новости. Пожалуйста, попробуйте позже.</p>
                <button onclick="history.back()">Вернуться назад</button>
            </div>
        `;
    }
}

async function loadSourcePage(container, source) {
    const sourceNames = {
        "news": "Новостные сайты",
        "social": "Социальные сети",
        "stat": "Google search"
    };
    
    container.innerHTML = '<div class="loading-spinner">Загрузка новостей...</div>';
    
    try {
        const articles = await fetchArticles(10, null, source);
        const sourceName = sourceNames[source] || "Источник";

        let html = `
            <section class="digest">
                <h2>Новости дня</h2>
                <ul>
        `;

        articles.slice(0, 3).forEach(article => {
            html += `<li><a href="#" data-article="${article._id}">${article.title}</a></li>`;
        });

        html += `
                </ul>
            </section>
            <section class="latest-news">
                <h2>Источник: ${sourceName}</h2>
        `;

        articles.forEach(article => {
            html += `
                <div class="news-item">
                    <img src="${article.image || 'foto.jpg'}" alt="${article.title}">
                    <div class="news-text">
                        <a href="#" data-article="${article._id}" class="news-title">${article.title}</a>
                        <p>${article.summary || 'Описание новости отсутствует'}</p>
                        <small>Источник: ${article.source || 'неизвестен'}</small>
                    </div>
                </div>
            `;
        });

        html += `</section>`;
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `
            <div class="error-message">
                <p>Не удалось загрузить новости. Пожалуйста, попробуйте позже.</p>
                <button onclick="history.back()">Вернуться назад</button>
            </div>
        `;
    }
}

async function loadArticle(articleId) {
    const contentContainer = document.getElementById('dynamic-content');
    contentContainer.innerHTML = '<div class="loading-spinner">Загрузка статьи...</div>';
    
    try {
        const article = await fetchArticleById(articleId);
        
        if (!article) {
            throw new Error('Статья не найдена');
        }
        
        history.pushState({ page: 'article', type: articleId }, '', `?page=article&id=${articleId}`);

        contentContainer.innerHTML = `
            <div class="news-article">
                <div class="article-text">
                    <h2 class="headline">${article.title}</h2>
                    <div class="article-meta">
                        <span class="article-date">${formatDate(article.publication_date)}</span>
                        <span class="article-source">${article.source || ''}</span>
                    </div>
                    <div class="article-content">${article.content || 'Содержание статьи отсутствует'}</div>
                </div>
                <div class="article-image">
                    <img src="${article.image || 'foto.jpg'}" alt="Фотография новости">
                </div>
            </div>
        `;
    } catch (error) {
        contentContainer.innerHTML = `
            <div class="error-message">
                <p>Не удалось загрузить статью. Пожалуйста, попробуйте позже.</p>
                <p class="error-details">${error.message}</p>
                <button onclick="history.back()">Вернуться назад</button>
            </div>
        `;
    }
}

async function loadArticlePage(container, articleId) {
    await loadArticle(articleId);
}

// ========== Search Functions ==========
function initSearch() {
    const searchInput = document.querySelector('.search-input');
    const searchButton = document.querySelector('.search-button');
    
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = this.value.trim();
                if (query) {
                    performSearch(query);
                }
            }
        });
    }
    
    if (searchButton) {
        searchButton.addEventListener('click', function() {
            const query = searchInput.value.trim();
            if (query) {
                performSearch(query);
            }
        });
    }
}

async function performSearch(query) {
    try {
        const contentContainer = document.getElementById('dynamic-content');
        contentContainer.innerHTML = `
            <div class="search-loading">
                <div class="spinner"></div>
                <p>Ищем новости по запросу: "${query}"</p>
            </div>
        `;

        const results = await searchArticles(query);
        
        const processedResults = results.map(item => ({
            id: item._id,
            title: item.title,
            description: item.summary || item.source || '',
            image: item.image || 'foto.jpg',
            url: item.url || '#',
            date: formatDate(item.publication_date),
            source: item.source || 'неизвестен'
        }));

        sessionStorage.setItem('searchResults', JSON.stringify({
            query: query,
            results: processedResults
        }));

        history.pushState({ page: 'search', query: query }, '', `?page=search&query=${encodeURIComponent(query)}`);
        await loadSearchResultsPage(contentContainer, query);
        
    } catch (error) {
        const contentContainer = document.getElementById('dynamic-content');
        contentContainer.innerHTML = `
            <div class="search-error">
                <h2>Ошибка при поиске</h2>
                <p>Произошла ошибка при выполнении поиска. Пожалуйста, попробуйте позже.</p>
                <p class="error-details">${error.message}</p>
                <button onclick="history.back()">Вернуться назад</button>
            </div>
        `;
    }
}

async function loadSearchResultsPage(container, query) {
    let searchData = { query: query || '', results: [] };
    
    try {
        const savedData = sessionStorage.getItem('searchResults');
        if (savedData) {
            searchData = JSON.parse(savedData);
        }
    } catch (e) {
        console.error('Error parsing search results:', e);
    }

    let html = `
        <div class="search-results-container">
            <h2 class="search-title">Результаты поиска: "${searchData.query}"</h2>
            <div class="results-count">Найдено статей: ${searchData.results.length}</div>
    `;

    if (searchData.results.length > 0) {
        html += '<div class="results-list">';
        searchData.results.forEach(item => {
            html += `
                <div class="search-item">
                    <div class="search-item-header">
                        <a href="${item.url}" target="_blank" class="search-item-title">${item.title}</a>
                        <span class="search-item-date">${item.date}</span>
                    </div>
                    <p class="search-item-desc">${item.description}</p>
                    <div class="search-item-footer">
                        <span class="search-item-source">${item.source}</span>
                    </div>
                </div>
            `;
        });
        html += '</div>';
    } else {
        html += `
            <div class="no-results">
                <p>По запросу "${searchData.query}" ничего не найдено.</p>
                <p>Попробуйте изменить формулировку запроса.</p>
                <button onclick="history.back()">Вернуться назад</button>
            </div>
        `;
    }

    html += '</div>';
    container.innerHTML = html;
}

// ========== Helper Functions ==========
function formatDate(dateString) {
    if (!dateString) return 'Дата неизвестна';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        });
    } catch (e) {
        return 'Дата неизвестна';
    }
}

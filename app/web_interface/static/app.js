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

async function fetchArticles() {
    try {
        const response = await fetch('http://localhost:8000/api/articles');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching articles:', error);
        return [];
    }
}

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

function loadPage(params) {
    const { page, type, query } = params;
    const contentContainer = document.getElementById('dynamic-content');
    
    switch(page) {
        case 'main':
            loadMainPage(contentContainer);
            break;
        case 'category':
            loadCategoryPage(contentContainer, type);
            break;
        case 'source':
            loadSourcePage(contentContainer, type);
            break;
        case 'article':
            loadArticlePage(contentContainer, type);
            break;
        case 'search':
            loadSearchResultsPage(contentContainer, query);
            break;
        default:
            loadMainPage(contentContainer);
    }
}

async function loadMainPage(container) {
    const articles = await fetchArticles();
    const latestArticles = articles.slice(0, 3);
    const dayNews = articles.slice(0, 3);
    
    let digestHTML = `
        <section class="digest">
            <h2>Новости дня</h2>
            <ul>
    `;
    
    dayNews.forEach(article => {
        digestHTML += `<li><a href="#" data-article="${article._id}">${article.title}</a></li>`;
    });
    
    digestHTML += `
            </ul>
        </section>
        <section class="latest-news">
            <h2>Последние новости</h2>
    `;
    
    latestArticles.forEach(article => {
        digestHTML += `
            <div class="news-item">
                <img src="foto.jpg" alt="">
                <div class="news-text">
                    <a href="#" data-article="${article._id}" class="news-title">${article.title}</a>
                    <p>${article.summary || 'Описание отсутствует'}</p>
                </div>
            </div>
        `;
    });
    
    digestHTML += `</section>`;
    container.innerHTML = digestHTML;
}

async function loadCategoryPage(container, category) {
    const categoryNames = {
        "culture": "Культура",
        "sports": "Спорт",
        "tech": "Технологии",
        "holidays": "Праздники",
        "education": "Образование"
    };

    const articles = await fetchArticles();
    const categoryArticles = articles.filter(article => article.category === category);
    const categoryName = categoryNames[category] || "Категория";

    let digestHTML = `
        <section class="digest">
            <h2>Новости дня</h2>
            <ul>
    `;

    categoryArticles.slice(0, 3).forEach(article => {
        digestHTML += `<li><a href="#" data-article="${article._id}">${article.title}</a></li>`;
    });

    digestHTML += `
            </ul>
        </section>
        <section class="latest-news">
            <h2>Новости: ${categoryName}</h2>
    `;

    categoryArticles.forEach(article => {
        digestHTML += `
            <div class="news-item">
                <img src="foto.jpg" alt="">
                <div class="news-text">
                    <a href="#" data-article="${article._id}" class="news-title">${article.title}</a>
                    <p>${article.summary || 'Описание отсутствует'}</p>
                </div>
            </div>
        `;
    });

    digestHTML += `</section>`;
    container.innerHTML = digestHTML;
}

async function loadSourcePage(container, source) {
    const sourceNames = {
        "news": "Новостные сайты",
        "social": "Социальные сети",
        "stat": "Google search"
    };

    const articles = await fetchArticles();
    const sourceArticles = articles.filter(article => article.source === source);
    const sourceName = sourceNames[source] || "Источник";

    let html = `
        <section class="digest">
            <h2>Новости дня</h2>
            <ul>
    `;

    sourceArticles.slice(0, 3).forEach(article => {
        html += `<li><a href="#" data-article="${article._id}">${article.title}</a></li>`;
    });

    html += `
            </ul>
        </section>
        <section class="latest-news">
            <h2>Источник: ${sourceName}</h2>
    `;

    sourceArticles.forEach(article => {
        html += `
            <div class="news-item">
                <img src="foto.jpg" alt="">
                <div class="news-text">
                    <a href="#" data-article="${article._id}" class="news-title">${article.title}</a>
                    <p>${article.summary || 'Описание отсутствует'}</p>
                    <small>Источник: ${article.source || 'неизвестен'}</small>
                </div>
            </div>
        `;
    });

    html += `</section>`;
    container.innerHTML = html;
}

async function loadArticle(articleId) {
    try {
        const response = await fetch(`http://localhost:8000/api/articles/${articleId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const article = await response.json();
        
        const contentContainer = document.getElementById('dynamic-content');
        history.pushState({ page: 'article', type: articleId }, '', `?page=article&id=${articleId}`);

        contentContainer.innerHTML = `
            <div class="news-article">
                <div class="article-text">
                    <h2 class="headline">${article.title}</h2>
                    <p>${article.content || 'Содержание отсутствует'}</p>
                </div>
                <div class="article-image">
                    <img src="foto.jpg" alt="Фотография новости">
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading article:', error);
        const contentContainer = document.getElementById('dynamic-content');
        contentContainer.innerHTML = `
            <div class="error-message">
                <h2>Ошибка загрузки статьи</h2>
                <p>Не удалось загрузить запрошенную статью. Пожалуйста, попробуйте позже.</p>
            </div>
        `;
    }
}

function loadArticlePage(container, articleId) {
    loadArticle(articleId);
}

async function performSearch(query) {
    try {
        // Показываем индикатор загрузки
        const contentContainer = document.getElementById('dynamic-content');
        contentContainer.innerHTML = `
            <div class="search-loading">
                <div class="spinner"></div>
                <p>Ищем новости по запросу: "${query}"</p>
            </div>
        `;

        const response = await fetch(`http://localhost:8000/api/search?query=${encodeURIComponent(query)}`);
        
        if (!response.ok) {
            throw new Error(`Ошибка HTTP! Статус: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Обработка результатов из MongoDB
        const results = data.map(item => ({
            id: item._id?.$oid || item._id || Math.random().toString(36).substr(2, 9),
            title: item.title,
            description: item.summary || item.source || '',
            img: "foto.jpg",
            url: item.url,
            date: item.publication_date ? 
                new Date(item.publication_date.$date || item.publication_date).toLocaleDateString('ru-RU') : 
                'Дата неизвестна',
            source: item.source || 'неизвестен'
        }));

        // Сохраняем результаты
        sessionStorage.setItem('searchResults', JSON.stringify({
            query: query,
            results: results
        }));

        // Обновляем URL и загружаем страницу с результатами
        history.pushState({ page: 'search', query: query }, '', `?page=search&query=${encodeURIComponent(query)}`);
        loadSearchResultsPage(contentContainer, query);
        
    } catch (error) {
        console.error("Search error:", error);
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

function loadSearchResultsPage(container, query) {
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

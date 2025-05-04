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
        
        if (e.target.matches('.search-item-title') && e.target.href) {
            return;
        }
    });

    // Инициализация поиска
    initSearch();
});

// Функция для загрузки данных из API
async function fetchArticles(limit = 5, category = null) {
    try {
        let url = `http://localhost:8000/api/articles?limit=${limit}`;
        if (category) {
            url += `&category=${category}`;
        }
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching articles:', error);
        return [];
    }
}

async function fetchArticleById(id) {
    try {
        const response = await fetch(`http://localhost:8000/api/articles/${id}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching article:', error);
        return null;
    }
}

// Обновленная функция для загрузки главной страницы
async function loadMainPage(container) {
    // Показываем индикатор загрузки
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
                        <p>${article.summary || 'Описание отсутствует'}</p>
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
                <p>${error.message}</p>
            </div>
        `;
    }
}

// Обновленная функция для загрузки страницы категории
async function loadCategoryPage(container, category) {
    const categoryNames = {
        "culture": "Культура",
        "sports": "Спорт",
        "tech": "Технологии",
        "holidays": "Праздники",
        "education": "Образование"
    };

    // Показываем индикатор загрузки
    container.innerHTML = '<div class="loading-spinner">Загрузка новостей...</div>';
    
    try {
        const articles = await fetchArticles(5, category);
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
                        <p>${article.summary || 'Описание отсутствует'}</p>
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
                <p>${error.message}</p>
            </div>
        `;
    }
}

// Обновленная функция для загрузки статьи
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
                    <p class="article-meta">
                        <span class="article-date">${new Date(article.publication_date).toLocaleDateString('ru-RU')}</span>
                        <span class="article-source">Источник: ${article.source || 'неизвестен'}</span>
                    </p>
                    <div class="article-content">${article.text || 'Содержимое статьи отсутствует'}</div>
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
                <p>${error.message}</p>
                <button onclick="history.back()">Вернуться назад</button>
            </div>
        `;
    }
}

// Остальные функции остаются без изменений
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

function loadSourcePage(container, source) {
    const sourceNames = {
        "news": "Новостные сайты",
        "social": "Социальные сети",
        "stat": "Google search"
    };

    const newsData = {
        "news": [
            { id: 6, img: "foto.jpg", title: "Заголовок новости", description: "Описание новости.", source: "Официальный сайт" },
            { id: 7, img: "foto.jpg", title: "Заголовок новости", description: "Описание второй новости.", source: "Газета" }
        ],
        "social": [
            { id: 8, img: "foto.jpg", title: "Обсуждение в соцсетях", description: "Тема, обсуждаемая в соцсетях.", source: "ВКонтакте" },
            { id: 9, img: "foto.jpg", title: "Новость из Telegram", description: "Что обсуждают в Telegram.", source: "Telegram" }
        ]
    };

    const currentNews = newsData[source] || [];
    const sourceName = sourceNames[source] || "Источник";

    let html = `
        <section class="digest">
            <h2>Новости дня</h2>
            <ul>
    `;

    currentNews.slice(0, 3).forEach(news => {
        html += `<li><a href="#" data-article="${news.id}">${news.title}</a></li>`;
    });

    html += `
            </ul>
        </section>
        <section class="latest-news">
            <h2>Источник: ${sourceName}</h2>
    `;

    currentNews.forEach(news => {
        html += `
            <div class="news-item">
                <img src="${news.img}" alt="">
                <div class="news-text">
                    <a href="#" data-article="${news.id}" class="news-title">${news.title}</a>
                    <p>${news.description}</p>
                    <small>Источник: ${news.source}</small>
                </div>
            </div>
        `;
    });

    html += `</section>`;
    container.innerHTML = html;
}

function loadArticlePage(container, articleId) {
    loadArticle(articleId);
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

        const response = await fetch(`http://localhost:8000/api/search?query=${encodeURIComponent(query)}`);
        
        if (!response.ok) {
            throw new Error(`Ошибка HTTP! Статус: ${response.status}`);
        }
        
        const data = await response.json();
        
        const results = data.map(item => ({
            id: item._id?.$oid || item._id || Math.random().toString(36).substr(2, 9),
            title: item.title,
            description: item.summary || item.source || '',
            img: item.image || "foto.jpg",
            url: item.url,
            date: item.publication_date ? 
                new Date(item.publication_date.$date || item.publication_date).toLocaleDateString('ru-RU') : 
                'Дата неизвестна',
            source: item.source || 'неизвестен'
        }));

        sessionStorage.setItem('searchResults', JSON.stringify({
            query: query,
            results: results
        }));

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

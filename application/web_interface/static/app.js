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
            return;
        }
    });

    // Инициализация поиска
    initSearch();
});

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

// Глобальные переменные для пагинации
let currentNewsPage = 1;
const newsPerPage = 5;
let allNewsData = [];

async function loadMainPage(container) {
    try {
        container.innerHTML = '<div class="loading-spinner">Загрузка новостей...</div>';

        const response = await fetch('http://78.36.44.126:8000/api/latest-news');

        if (!response.ok) {
            throw new Error(`Ошибка HTTP! Статус: ${response.status}`);
        }

        allNewsData = await response.json();
        currentNewsPage = 1; // Сбрасываем на первую страницу

        renderMainPageContent(container);

    } catch (error) {
        console.error("Ошибка при загрузке новостей:", error);
        container.innerHTML = `
            <div class="error-message">
                <h2>Ошибка при загрузке новостей</h2>
                <p>${error.message}</p>
                <button onclick="location.reload()">Попробовать снова</button>
            </div>
        `;
    }
}

function renderMainPageContent(container) {
    // Создаем HTML для блока "Новости дня"
    const digestHTML = `
        <section class="digest">
            <h2>Новости дня</h2>
            <ul>
                ${allNewsData.slice(0, 3).map(item =>
                    `<li><a href="#" data-article="${item._id.$oid}">${item.title}</a></li>`
                ).join('')}
            </ul>
        </section>
        <section class="latest-news">
            <h2>Последние новости</h2>
            <div id="news-list-container"></div>
            <div id="news-pagination"></div>
        </section>
    `;

    container.innerHTML = digestHTML;

    // Рендерим список новостей и пагинацию
    renderNewsList();
    renderPagination();
}

function renderNewsList() {
    const startIndex = (currentNewsPage - 1) * newsPerPage;
    const paginatedNews = allNewsData.slice(startIndex, startIndex + newsPerPage);
    const newsContainer = document.getElementById('news-list-container');

    if (!newsContainer) return;

    newsContainer.innerHTML = paginatedNews.map(item => {
        const date = item.publication_date ?
            new Date(item.publication_date.$date).toLocaleDateString('ru-RU') :
            'Дата неизвестна';

        return `
            <div class="news-item">
                <img src="foto.jpg" alt="${item.title}">
                <div class="news-text">
                    <a href="#" data-article="${item._id.$oid}" class="news-title">${item.title}</a>
                    <p>${item.summary || 'Нет описания'}</p>
                    <small>Дата публикации: ${date}</small>
                </div>
            </div>
        `;
    }).join('');
}

function renderPagination() {
    const totalPages = Math.ceil(allNewsData.length / newsPerPage);
    const paginationContainer = document.getElementById('news-pagination');

    if (!paginationContainer || totalPages <= 1) {
        if (paginationContainer) paginationContainer.innerHTML = '';
        return;
    }

    let paginationHTML = '<div class="pagination">';

    // Кнопка "Назад"
    if (currentNewsPage > 1) {
        paginationHTML += `
            <button class="page-btn" onclick="changeNewsPage(${currentNewsPage - 1})">
                ← Назад
            </button>
        `;
    }

    // Номера страниц
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentNewsPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    if (endPage - startPage + 1 < maxVisiblePages) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    if (startPage > 1) {
        paginationHTML += `<button class="page-btn" onclick="changeNewsPage(1)">1</button>`;
        if (startPage > 2) {
            paginationHTML += `<span class="page-dots">...</span>`;
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        if (i === currentNewsPage) {
            paginationHTML += `<span class="current-page">${i}</span>`;
        } else {
            paginationHTML += `<button class="page-btn" onclick="changeNewsPage(${i})">${i}</button>`;
        }
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHTML += `<span class="page-dots">...</span>`;
        }
        paginationHTML += `<button class="page-btn" onclick="changeNewsPage(${totalPages})">${totalPages}</button>`;
    }

    // Кнопка "Вперед"
    if (currentNewsPage < totalPages) {
        paginationHTML += `
            <button class="page-btn" onclick="changeNewsPage(${currentNewsPage + 1})">
                Вперед →
            </button>
        `;
    }

    paginationHTML += '</div>';
    paginationContainer.innerHTML = paginationHTML;
}

// Функция для смены страницы (должна быть в глобальной области видимости)
window.changeNewsPage = function(newPage) {
    currentNewsPage = newPage;
    renderNewsList();
    renderPagination();
    window.scrollTo({ top: 0, behavior: 'smooth' });
};

async function loadCategoryPage(container, category) {
    try {
        container.innerHTML = '<div class="loading-spinner">Загрузка новостей...</div>';

        const response = await fetch(`http://78.36.44.126:8000/api/category/${category}`);

        if (!response.ok) {
            throw new Error(`Ошибка HTTP! Статус: ${response.status}`);
        }

        const news = await response.json();
        const categoryNames = {
            "culture": "Культура",
            "sports": "Спорт",
            "tech": "Технологии",
            "holidays": "Праздники",
            "education": "Образование"
        };

        const categoryName = categoryNames[category] || "Категория";

        let html = `
            <section class="digest">
                <h2>Новости дня</h2>
                <ul>
        `;

        news.slice(0, 3).forEach(item => {
            html += `<li><a href="#" data-article="${item._id.$oid}">${item.title}</a></li>`;
        });

        html += `
                </ul>
            </section>
            <section class="latest-news">
                <h2>Новости: ${categoryName}</h2>
        `;

        news.forEach(item => {
            const date = item.publication_date ?
                new Date(item.publication_date.$date).toLocaleDateString('ru-RU') :
                'Дата неизвестна';

            html += `
                <div class="news-item">
                    <img src="foto.jpg" alt="${item.title}">
                    <div class="news-text">
                        <a href="#" data-article="${item._id.$oid}" class="news-title">${item.title}</a>
                        <p>${item.summary || 'Нет описания'}</p>
                        <small>Дата публикации: ${date}</small>
                    </div>
                </div>
            `;
        });

        html += `</section>`;
        container.innerHTML = html;

    } catch (error) {
        console.error("Ошибка при загрузке категории:", error);
        container.innerHTML = `
            <div class="error-message">
                <h2>Ошибка при загрузке категории</h2>
                <p>${error.message}</p>
                <button onclick="history.back()">Вернуться назад</button>
            </div>
        `;
    }
}

async function loadSourcePage(container, source) {
    try {
        container.innerHTML = '<div class="loading-spinner">Загрузка новостей...</div>';

        const response = await fetch(`http://78.36.44.126:8000/api/source/${source}`);

        if (!response.ok) {
            throw new Error(`Ошибка HTTP! Статус: ${response.status}`);
        }

        const news = await response.json();
        const sourceNames = {
            "news": "Новостные сайты",
            "social": "Социальные сети",
            "stat": "Google search"
        };

        const sourceName = sourceNames[source] || "Источник";

        let html = `
            <section class="digest">
                <h2>Новости дня</h2>
                <ul>
        `;

        news.slice(0, 3).forEach(item => {
            html += `<li><a href="#" data-article="${item._id.$oid}">${item.title}</a></li>`;
        });

        html += `
                </ul>
            </section>
            <section class="latest-news">
                <h2>Источник: ${sourceName}</h2>
        `;

        news.forEach(item => {
            const date = item.publication_date ?
                new Date(item.publication_date.$date).toLocaleDateString('ru-RU') :
                'Дата неизвестна';

            html += `
                <div class="news-item">
                    <img src="foto.jpg" alt="${item.title}">
                    <div class="news-text">
                        <a href="#" data-article="${item._id.$oid}" class="news-title">${item.title}</a>
                        <p>${item.summary || 'Нет описания'}</p>
                        <small>Дата публикации: ${date}</small>
                        <small>Источник: ${item.source || 'неизвестен'}</small>
                    </div>
                </div>
            `;
        });

        html += `</section>`;
        container.innerHTML = html;

    } catch (error) {
        console.error("Ошибка при загрузке источника:", error);
        container.innerHTML = `
            <div class="error-message">
                <h2>Ошибка при загрузке источника</h2>
                <p>${error.message}</p>
                <button onclick="history.back()">Вернуться назад</button>
            </div>
        `;
    }
}

async function loadArticle(articleId) {
    try {
        const contentContainer = document.getElementById('dynamic-content');
        contentContainer.innerHTML = '<div class="loading-spinner">Загрузка статьи...</div>';

        const response = await fetch(`http://78.36.44.126:8000/api/article/${articleId}`);

        if (!response.ok) {
            throw new Error(`Ошибка HTTP! Статус: ${response.status}`);
        }

        const article = await response.json();

        const pubDate = article.publication_date ?
            new Date(article.publication_date.$date).toLocaleDateString('ru-RU', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                weekday: 'long'
            }) :
            'Дата неизвестна';

        history.pushState({ page: 'article', type: articleId }, '', `?page=article&id=${articleId}`);

        contentContainer.innerHTML = `
            <div class="news-article">
                <div class="article-text">
                    <h2 class="headline">${article.title}</h2>
                    <div class="article-meta">
                        <span class="article-date">${pubDate}</span>
                        ${article.source ? `<span class="article-source">Источник: ${article.source}</span>` : ''}
                    </div>
                    <div class="article-content">${article.text || 'Содержание отсутствует'}</div>
                </div>
                <div class="article-image">
                    <img src="foto.jpg" alt="Фотография новости">
                </div>
            </div>
        `;
    } catch (error) {
        console.error("Ошибка при загрузке статьи:", error);
        const contentContainer = document.getElementById('dynamic-content');
        contentContainer.innerHTML = `
            <div class="error-message">
                <h2>Ошибка при загрузке статьи</h2>
                <p>${error.message}</p>
                <button onclick="history.back()">Вернуться назад</button>
            </div>
        `;
    }
}

async function loadArticlePage(container, articleId) {
    await loadArticle(articleId);
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

        const response = await fetch(`http://78.36.44.126:8000/api/search?query=${encodeURIComponent(query)}`);

        if (!response.ok) {
            throw new Error(`Ошибка HTTP! Статус: ${response.status}`);
        }

        const data = await response.json();

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

        sessionStorage.setItem('searchResults', JSON.stringify({
            query: query,
            results: results
        }));

        history.pushState({ page: 'search', query: query }, '', `?page=search&query=${encodeURIComponent(query)}`);
        await loadSearchResultsPage(contentContainer, query);

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

async function loadCategoryPage(container, category) {
    try {
        container.innerHTML = '<div class="loading-spinner">Загрузка новостей...</div>';

        const response = await fetch(`${API_BASE_URL}/api/category/${category}`);

        if (!response.ok) {
            throw new Error(`Ошибка HTTP! Статус: ${response.status}`);
        }

        const news = await response.json();
        const categoryData = {
            "culture": {
                name: "Культура",
                icon: "🎭",
                description: "Новости из мира искусства, кино, музыки и литературы"
            },
            "sports": {
                name: "Спорт",
                icon: "⚽",
                description: "Спортивные события, матчи и турниры"
            },
            "tech": {
                name: "Технологии",
                icon: "💻",
                description: "IT-новости, гаджеты и научные разработки"
            },
            "holidays": {
                name: "Праздники",
                icon: "🎉",
                description: "Праздничные события и традиции"
            },
            "education": {
                name: "Образование",
                icon: "📚",
                description: "Новости образования и науки"
            }
        };

        const currentCategory = categoryData[category] || {
            name: "Категория",
            icon: "📁",
            description: "Новости по выбранной категории"
        };

        let html = `
            <div class="category-header">
                <div class="category-icon">${currentCategory.icon}</div>
                <div class="category-info">
                    <h1>${currentCategory.name}</h1>
                    <p class="category-description">${currentCategory.description}</p>
                </div>
            </div>
            
            <div class="category-content">
                <section class="top-news">
                    <h2><i class="icon-star"></i> Топ новости</h2>
                    <div class="top-news-grid">
        `;

        // Топ 3 новости
        news.slice(0, 3).forEach(item => {
            const date = item.publication_date ?
                new Date(item.publication_date.$date).toLocaleDateString('ru-RU') :
                'Дата неизвестна';

            html += `
                <div class="top-news-item">
                    <div class="top-news-image">
                        <img src="foto.jpg" alt="${item.title}">
                    </div>
                    <div class="top-news-content">
                        <a href="#" data-article="${item._id.$oid}" class="top-news-title">${item.title}</a>
                        <p class="top-news-summary">${item.summary || 'Нет описания'}</p>
                        <div class="top-news-meta">
                            <span class="top-news-date">${date}</span>
                            ${item.source ? `<span class="top-news-source">${item.source}</span>` : ''}
                        </div>
                    </div>
                </div>
            `;
        });

        html += `
                    </div>
                </section>
                
                <section class="all-category-news">
                    <h2><i class="icon-list"></i> Все новости категории</h2>
                    <div class="category-news-list">
        `;

        // Все остальные новости
        news.slice(3).forEach(item => {
            const date = item.publication_date ?
                new Date(item.publication_date.$date).toLocaleDateString('ru-RU') :
                'Дата неизвестна';

            html += `
                <div class="category-news-item">
                    <div class="category-news-text">
                        <a href="#" data-article="${item._id.$oid}" class="category-news-title">${item.title}</a>
                        <p class="category-news-summary">${item.summary || 'Нет описания'}</p>
                        <div class="category-news-meta">
                            <span class="category-news-date">${date}</span>
                            ${item.source ? `<span class="category-news-source">${item.source}</span>` : ''}
                        </div>
                    </div>
                    <div class="category-news-image">
                        <img src="foto.jpg" alt="${item.title}">
                    </div>
                </div>
            `;
        });

        html += `
                    </div>
                </section>
            </div>
        `;

        container.innerHTML = html;

    } catch (error) {
        console.error("Ошибка при загрузке категории:", error);
        container.innerHTML = `
            <div class="error-message">
                <h2>Ошибка при загрузке категории</h2>
                <p>${error.message}</p>
                <button onclick="history.back()">Вернуться назад</button>
            </div>
        `;
    }
}
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

// Добавляем глобальные переменные для фильтрации
let currentFilters = {
    category: null,
    location: null
};

// Модифицируем функцию loadMainPage для поддержки фильтрации
async function loadMainPage(container, filters = {}) {
    try {
        container.innerHTML = '<div class="loading-spinner">Загрузка новостей...</div>';

        // Формируем URL с учетом фильтров
        let url = 'http://78.36.44.126:8000/api/latest-news';
        const queryParams = [];

        if (filters.category) {
            queryParams.push(`category=${encodeURIComponent(filters.category)}`);
        }
        if (filters.location) {
            queryParams.push(`location=${encodeURIComponent(filters.location)}`);
        }

        if (queryParams.length > 0) {
            url += `?${queryParams.join('&')}`;
        }

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`Ошибка HTTP! Статус: ${response.status}`);
        }

        allNewsData = await response.json();
        currentNewsPage = 1;

        renderMainPageContent(container, filters);

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

// Обновляем renderMainPageContent для отображения фильтров
function renderMainPageContent(container, filters) {
    const digestHTML = `
        <section class="digest">
            <h2>Новости дня</h2>
            <div class="filters">
                <select id="category-filter" class="filter-select">
                    <option value="">Все категории</option>
                    <option value="culture">Культура</option>
                    <option value="sports">Спорт</option>
                    <option value="tech">Технологии</option>
                    <option value="holidays">Праздники</option>
                    <option value="education">Образование</option>
                </select>
                
                <select id="location-filter" class="filter-select">
                    <option value="">Все локации</option>
                    <option value="Петрозаводск">Петрозаводск</option>
                    <option value="Беломорск">Беломорск</option>
                    <option value="Сортавала">Сортавала</option>
                    <!-- Добавьте другие локации -->
                </select>
                
                <button id="apply-filters" class="filter-button">Применить</button>
                ${filters.category || filters.location ? 
                    `<button id="reset-filters" class="filter-button">Сбросить</button>` : ''}
            </div>
            <ul>
                ${allNewsData.slice(0, 3).map(item =>
                    `<li><a href="#" data-article="${item._id.$oid}">${item.title}</a></li>`
                ).join('')}
            </ul>
        </section>
        <section class="latest-news">
            <h2>${getFilterTitle(filters)}</h2>
            <div id="news-list-container"></div>
            <div id="news-pagination"></div>
        </section>
    `;

    container.innerHTML = digestHTML;

    // Устанавливаем текущие значения фильтров
    if (filters.category) {
        document.getElementById('category-filter').value = filters.category;
    }
    if (filters.location) {
        document.getElementById('location-filter').value = filters.location;
    }

    // Навешиваем обработчики на фильтры
    setupFilterHandlers();

    renderNewsList();
    renderPagination();
}

// Вспомогательная функция для заголовка раздела
function getFilterTitle(filters) {
    if (filters.category && filters.location) {
        return `Новости: ${getCategoryName(filters.category)} (${filters.location})`;
    }
    if (filters.category) {
        return `Новости: ${getCategoryName(filters.category)}`;
    }
    if (filters.location) {
        return `Новости в ${filters.location}`;
    }
    return 'Последние новости';
}

function getCategoryName(category) {
    const names = {
        "culture": "Культура",
        "sports": "Спорт",
        "tech": "Технологии",
        "holidays": "Праздники",
        "education": "Образование"
    };
    return names[category] || category;
}

// Настройка обработчиков фильтров
function setupFilterHandlers() {
    const applyBtn = document.getElementById('apply-filters');
    const resetBtn = document.getElementById('reset-filters');

    if (applyBtn) {
        applyBtn.addEventListener('click', () => {
            const category = document.getElementById('category-filter').value;
            const location = document.getElementById('location-filter').value;

            const filters = {};
            if (category) filters.category = category;
            if (location) filters.location = location;

            currentFilters = filters;
            loadMainPage(document.getElementById('dynamic-content'), filters);
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            currentFilters = {};
            loadMainPage(document.getElementById('dynamic-content'), {});
        });
    }
}

// Модифицируем функцию loadPage для передачи фильтров
async function loadPage(params) {
    const { page, type, query } = params;
    const contentContainer = document.getElementById('dynamic-content');

    switch(page) {
        case 'main':
            await loadMainPage(contentContainer, currentFilters);
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
            await loadMainPage(contentContainer, currentFilters);
    }
}

// Обновляем функцию initSearch для поддержки фильтрации в поиске
function initSearch() {
    const searchInput = document.querySelector('.search-input');
    const searchButton = document.querySelector('.search-button');

    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = this.value.trim();
                if (query) {
                    performSearch(query, currentFilters);
                }
            }
        });
    }

    if (searchButton) {
        searchButton.addEventListener('click', function() {
            const query = searchInput.value.trim();
            if (query) {
                performSearch(query, currentFilters);
            }
        });
    }
}

// Модифицируем performSearch для поддержки фильтров
async function performSearch(query, filters = {}) {
    try {
        const contentContainer = document.getElementById('dynamic-content');
        contentContainer.innerHTML = `
            <div class="search-loading">
                <div class="spinner"></div>
                <p>Ищем новости по запросу: "${query}"</p>
            </div>
        `;

        // Формируем URL с учетом фильтров
        let url = `http://78.36.44.126:8000/api/search?query=${encodeURIComponent(query)}`;

        if (filters.category) {
            url += `&category=${encodeURIComponent(filters.category)}`;
        }
        if (filters.location) {
            url += `&location=${encodeURIComponent(filters.location)}`;
        }

        const response = await fetch(url);

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
            source: item.source || 'неизвестен',
            category: item.category || 'unknown'
        }));

        sessionStorage.setItem('searchResults', JSON.stringify({
            query: query,
            results: results,
            filters: filters
        }));

        history.pushState({ page: 'search', query: query, filters: filters }, '',
            `?page=search&query=${encodeURIComponent(query)}`);
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

// Обновляем loadSearchResultsPage для отображения фильтров
async function loadSearchResultsPage(container, query) {
    let searchData = { query: query || '', results: [], filters: {} };

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
            ${searchData.filters.category || searchData.filters.location ? 
                `<div class="active-filters">
                    Фильтры: 
                    ${searchData.filters.category ? `<span class="filter-tag">${getCategoryName(searchData.filters.category)}</span>` : ''}
                    ${searchData.filters.location ? `<span class="filter-tag">${searchData.filters.location}</span>` : ''}
                    <button class="clear-filters" onclick="clearSearchFilters()">×</button>
                </div>` : ''}
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
                        ${item.category !== 'unknown' ? `<span class="search-item-category">${getCategoryName(item.category)}</span>` : ''}
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
                ${searchData.filters.category || searchData.filters.location ? 
                    '<p>Попробуйте изменить параметры фильтров.</p>' : 
                    '<p>Попробуйте изменить формулировку запроса.</p>'}
                <button onclick="history.back()">Вернуться назад</button>
            </div>
        `;
    }

    html += '</div>';
    container.innerHTML = html;
}

// Добавляем глобальную функцию для сброса фильтров поиска
window.clearSearchFilters = function() {
    const searchData = JSON.parse(sessionStorage.getItem('searchResults') || {});
    performSearch(searchData.query);
};

// Обновляем обработчик DOMContentLoaded
document.addEventListener("DOMContentLoaded", function() {
    setCurrentDate();
    setupNavigation();

    // Получаем текущие параметры страницы
    const params = getCurrentPage();

    // Если есть параметры фильтров в URL, применяем их
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('category')) {
        currentFilters.category = urlParams.get('category');
    }
    if (urlParams.has('location')) {
        currentFilters.location = urlParams.get('location');
    }

    loadPage(params);

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
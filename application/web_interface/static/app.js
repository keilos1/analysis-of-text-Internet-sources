let API_BASE_URL = 'http://localhost:8000'; // Значение по умолчанию

// Инициализация приложения
document.addEventListener("DOMContentLoaded", async function() {
    // Загружаем конфигурацию
    try {
        const response = await fetch('/api/config');
        if (response.ok) {
            const config = await response.json();
            API_BASE_URL = `http://${config.SITE_HOST}:8000`;
            console.log('API base URL set to:', API_BASE_URL);
        }
    } catch (error) {
        console.error('Error loading config:', error);
    }

    // Инициализация приложения
    initApp();
});

function initApp() {
    setCurrentDate();
    setupNavigation();
    setupCategoryDropdown();
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

        const response = await fetch(`${API_BASE_URL}/api/latest-news`);

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
    const maxVisiblePages = 3;
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

async function loadCategoryPage(container, category, offset = 0, limit = 10) {
    try {
        // Показываем загрузчик
        document.getElementById('loader').style.display = 'block';

        // Если это первая загрузка, очищаем контейнер
        if (offset === 0) {
            container.innerHTML = '';
        }

        // Маппинг категорий
        const categoryMapping = {
            "culture": "Культура",
            "sports": "Спорт",
            "tech": "Технологии",
            "holidays": "Праздники",
            "education": "Образование",
            "other": "Другое"
        };

        const russianCategory = categoryMapping[category] || category;

        // Запрос статей по категории
        const response = await fetch(
            `${API_BASE_URL}/api/articles-by-category/${encodeURIComponent(russianCategory)}?offset=${offset}&limit=${limit}`
        );

        if (!response.ok) throw new Error(`Ошибка сервера: ${response.status}`);
        const { articles, total } = await response.json();

        // Если это первая загрузка, создаем основную структуру
        if (offset === 0) {
            container.innerHTML = `
                <div class="news-section full-width">
                    <h2 class="category-title">${russianCategory}</h2>
                    ${category === 'other' ? `<p class="category-description">Разные новости, не вошедшие в основные категории</p>` : ''}
                    <div class="news-grid-container"></div>
                </div>
            `;
        }

        const newsGrid = container.querySelector('.news-grid-container');

        // Добавление новых статей
        articles.forEach(article => {
            const pubDate = article.publication_date ?
                new Date(article.publication_date.$date).toLocaleDateString('ru-RU') :
                'Дата неизвестна';

            const articleItem = document.createElement('div');
            articleItem.className = 'news-item-full';
            articleItem.innerHTML = `
                <div class="news-image-container">
                    <img src="${article.image_url || 'foto.jpg'}" alt="${article.title}" class="news-image-fixed">
                </div>
                <div class="news-content-expanded">
                    <h3>
                        <a href="#" data-article="${article._id.$oid}" class="news-title">${article.title}</a>
                    </h3>
                    <p class="news-summary-expanded">${article.summary || 'Нет описания'}</p>
                    <div class="news-meta-expanded">
                        <span><i class="far fa-calendar-alt"></i> ${pubDate}</span>
                        ${article.categories?.length ? `
                            <span><i class="fas fa-tag"></i> ${article.categories.join(', ')}</span>
                        ` : ''}
                    </div>
                </div>
            `;
            newsGrid.appendChild(articleItem);
        });

        // Удаляем кнопку "Показать ещё", если она уже есть
        const existingLoadMoreBtn = container.querySelector('.load-more-btn');
        if (existingLoadMoreBtn) {
            existingLoadMoreBtn.remove();
        }

        // Добавляем кнопку "Показать ещё" только если есть еще статьи для загрузки
        if (articles.length === limit && offset + limit < total) {
            const loadMoreBtn = document.createElement('button');
            loadMoreBtn.className = 'load-more-btn';
            loadMoreBtn.innerHTML = '<i class="fas fa-plus"></i> Показать ещё';
            loadMoreBtn.addEventListener('click', () => {
                loadCategoryPage(container, category, offset + limit, limit);
            });
            container.querySelector('.news-section').appendChild(loadMoreBtn);
        }

        // Обработчики кликов по статьям
        container.querySelectorAll('[data-article]').forEach(link => {
            link.addEventListener('click', async (e) => {
                e.preventDefault();
                const articleId = e.currentTarget.getAttribute('data-article');
                await loadArticle(articleId);
            });
        });

    } catch (error) {
        console.error("Ошибка загрузки категории:", error);
        container.innerHTML = `
            <div class="error-message">
                <h2>Ошибка при загрузке категории</h2>
                <p>${error.message}</p>
                <div class="error-actions">
                    <button class="btn-back" onclick="history.back()">
                        <i class="fas fa-arrow-left"></i> Назад
                    </button>
                    <button class="btn-retry" onclick="loadCategoryPage(container, '${category}')">
                        <i class="fas fa-sync-alt"></i> Повторить
                    </button>
                </div>
            </div>
        `;
    } finally {
        document.getElementById('loader').style.display = 'none';
    }
}

function setupCategoryTabs() {
    document.querySelectorAll('.category-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            const category = this.dataset.category;

            // Обновляем активную вкладку
            document.querySelectorAll('.category-tab').forEach(t =>
                t.classList.toggle('active', t === this));

            // Показываем соответствующий контент
            document.querySelectorAll('.news-content').forEach(content => {
                content.style.display = content.dataset.category === category ? 'block' : 'none';
            });
        });
    });
}

function showError(container, title, message) {
    container.innerHTML = `
        <div class="error-message">
            <h2>${title}</h2>
            <p>${message}</p>
            <button onclick="history.back()">Вернуться назад</button>
        </div>
    `;
}

async function loadSourcePage(container, sourceType, offset = 0, limit = 10) {
    try {
        // Показываем загрузчик
        document.getElementById('loader').style.display = 'block';
        if (offset === 0) container.innerHTML = '';

        // Соответствие между типами и русскоязычными категориями
        const categoryMapping = {
            "news": "Новости",
            "social": "Соц. сети",
            "stat": "Google search"
        };

        const russianCategory = categoryMapping[sourceType];
        if (!russianCategory) {
            throw new Error("Неизвестный тип источника");
        }

        // Получаем данные с пагинацией
        const response = await fetch(
            `${API_BASE_URL}/api/sources-by-category/${encodeURIComponent(russianCategory)}?offset=${offset}&limit=${limit}`
        );
        if (!response.ok) throw new Error(`Ошибка сервера: ${response.status}`);
        const { articles, total } = await response.json();

        // Формируем HTML
        if (offset === 0) {
            container.innerHTML = `
                <div class="news-section full-width">
                    <h2 class="category-title">${getSourceTitle(russianCategory)}</h2>
                    <div class="news-grid-container"></div>
                </div>
            `;
        }

        const newsGrid = container.querySelector('.news-grid-container');

        // Добавляем новости
        articles.forEach(item => {
            const date = item.publication_date ?
                new Date(item.publication_date.$date).toLocaleDateString('ru-RU') :
                'Дата неизвестна';

            const newsItem = document.createElement('div');
            newsItem.className = 'news-item-full';
            newsItem.innerHTML = `
                <div class="news-image-container">
                    <img src="${item.image_url || 'foto.jpg'}" alt="${item.title}" class="news-image-fixed">
                </div>
                <div class="news-content-expanded">
                    <h3>
                        <a href="#" data-article="${item._id.$oid}", class="news-title">${item.title}</a>
                    </h3>
                    <p class="news-summary-expanded">${item.summary || 'Нет описания'}</p>
                    <div class="news-meta-expanded">
                        <span><i class="far fa-calendar-alt"></i> ${date}</span>
                        ${item.categories ? `
                            <span><i class="fas fa-tag"></i> ${formatCategories(item.categories)}</span>
                        ` : ''}
                    </div>
                </div>
            `;
            newsGrid.appendChild(newsItem);
        });

        // Добавляем кнопку "Показать еще" если есть еще новости
        if (offset + limit < total && !container.querySelector('.load-more-btn')) {
            const loadMoreBtn = document.createElement('button');
            loadMoreBtn.className = 'load-more-btn';
            loadMoreBtn.innerHTML = '<i class="fas fa-plus"></i> Показать еще';
            loadMoreBtn.addEventListener('click', () => {
                loadSourcePage(container, sourceType, offset + limit, limit);
            });
            container.querySelector('.news-section').appendChild(loadMoreBtn);
        }

        // Добавляем обработчики событий
        container.querySelectorAll('[data-article]').forEach(link => {
            link.addEventListener('click', async (e) => {
                e.preventDefault();
                const articleId = e.currentTarget.getAttribute('data-article');
                await loadArticle(articleId);
            });
        });

    } catch (error) {
        console.error("Ошибка загрузки:", error);
        container.innerHTML = `
            <div class="error-message">
                <h2>Ошибка при загрузке</h2>
                <p>${error.message}</p>
                <div class="error-actions">
                    <button class="btn-back" onclick="history.back()"><i class="fas fa-arrow-left"></i> Назад</button>
                    <button class="btn-retry" onclick="loadSourcePage(container, '${sourceType}')"><i class="fas fa-sync-alt"></i> Повторить</button>
                </div>
            </div>
        `;
    } finally {
        // Скрываем загрузчик
        document.getElementById('loader').style.display = 'none';
    }
}

// Вспомогательные функции
function getSourceTitle(category) {
    const titles = {
        "Новости": "Новостные сайты",
        "Соц. сети": "Социальные сети",
        "Google search": "Google Новости"
    };
    return titles[category] || category;
}

function formatCategories(categories) {
    if (Array.isArray(categories)) {
        return categories.join(', ');
    }
    return categories;
}

async function loadArticle(articleId) {
    try {
        const contentContainer = document.getElementById('dynamic-content');
        contentContainer.innerHTML = '<div class="loading-spinner">Загрузка статьи...</div>';

        const response = await fetch(`${API_BASE_URL}/api/article/${articleId}`);

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

        const response = await fetch(`${API_BASE_URL}/api/search?query=${encodeURIComponent(query)}`);

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

/**
 * Настраивает выпадающее меню категорий
 */
function setupCategoryDropdown() {
    const dropdownBtn = document.querySelector('.dropdown-btn');
    const dropdownContent = document.querySelector('.dropdown-content');

    if (!dropdownBtn || !dropdownContent) return;

    // Обработчик клика по кнопке
    dropdownBtn.addEventListener('click', (e) => {
        e.preventDefault();
        dropdownContent.classList.toggle('show');
    });

    // Обработчики для пунктов меню
    dropdownContent.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            // Закрываем меню после выбора
            dropdownContent.classList.remove('show');

            // Удаляем активный класс у всех пунктов
            dropdownContent.querySelectorAll('a').forEach(item => {
                item.classList.remove('active');
            });

            // Добавляем активный класс текущему пункту
            this.classList.add('active');

            // Обновляем текст кнопки на выбранную категорию
            dropdownBtn.textContent = this.textContent;

            // Получаем параметры из data-атрибутов
            const page = this.getAttribute('data-page');
            const type = this.getAttribute('data-type');

            // Обновляем URL и загружаем страницу
            const url = `?page=${page}&type=${type}`;
            history.pushState({ page, type }, '', url);
            loadPage({ page, type });
        });
    });

    // Закрытие меню при клике вне его
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.dropdown')) {
            dropdownContent.classList.remove('show');
        }
    });

    // Инициализация активного состояния при загрузке
    const currentPage = getCurrentPage();
    if (currentPage.page === 'category') {
        const activeLink = dropdownContent.querySelector(`a[data-type="${currentPage.type}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
            dropdownBtn.textContent = activeLink.textContent;
        }
    }
}
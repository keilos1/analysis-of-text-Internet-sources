document.addEventListener("DOMContentLoaded", function() {
    // Инициализация приложения
    initApp();
});

// Основные функции приложения
async function initApp() {
    setCurrentDate();
    setupNavigation();
    setupSearch();
    await loadMainContent();
}

// Установка текущей даты
function setCurrentDate() {
    const dateElement = document.getElementById("current-date");
    if (!dateElement) return;

    const today = new Date();
    const options = { 
        weekday: 'short', 
        day: 'numeric', 
        month: 'long', 
        year: 'numeric',
        timeZone: 'Europe/Moscow'
    };
    
    dateElement.textContent = today.toLocaleDateString('ru-RU', options);
}

// Настройка навигации
function setupNavigation() {
    document.querySelectorAll('[data-page]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.getAttribute('data-page');
            const type = this.getAttribute('data-type');
            loadContent(page, type);
        });
    });
}

// Настройка поиска
function setupSearch() {
    const searchInput = document.querySelector('.search-input');
    const searchIcon = document.querySelector('.search-icon');

    const performSearch = () => {
        const query = searchInput.value.trim();
        if (query) {
            loadSearchResults(query);
        }
    };

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performSearch();
    });

    searchIcon.addEventListener('click', performSearch);
}

// Загрузка основного контента
async function loadMainContent() {
    try {
        const [topArticles, latestNews] = await Promise.all([
            fetch('/api/top-articles').then(res => res.json()),
            fetch('/api/latest-news').then(res => res.json())
        ]);

        renderMainPage(topArticles, latestNews);
    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
        showError('Не удалось загрузить новости');
    }
}

// Рендер главной страницы
function renderMainPage(topArticles, latestNews) {
    const contentContainer = document.getElementById('dynamic-content');
    
    // Форматирование даты для новостей
    const formatDate = (dateString) => {
        const options = { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' };
        return new Date(dateString).toLocaleDateString('ru-RU', options);
    };

    contentContainer.innerHTML = `
        <section class="digest">
            <h2>Новости дня</h2>
            <ul>
                ${topArticles.map(article => `
                    <li>
                        <a href="#" data-page="article" data-type="${article._id}">
                            ${article.title} (${formatDate(article.publication_date)})
                        </a>
                    </li>
                `).join('')}
            </ul>
        </section>
        <section class="latest-news">
            <h2>Последние новости</h2>
            ${latestNews.map(article => `
                <div class="news-item">
                    <img src="${article.image || 'placeholder.jpg'}" alt="${article.title}">
                    <div class="news-text">
                        <a href="#" data-page="article" data-type="${article._id}" class="news-title">
                            ${article.title}
                        </a>
                        <p>${article.summary || 'Нет описания'}</p>
                        <small>${formatDate(article.publication_date)} • ${article.source}</small>
                    </div>
                </div>
            `).join('')}
        </section>
    `;
}

// Загрузка контента по страницам
async function loadContent(page, type) {
    const contentContainer = document.getElementById('dynamic-content');
    contentContainer.innerHTML = '<div class="loading">Загрузка...</div>';

    try {
        let html = '';
        
        switch(page) {
            case 'main':
                await loadMainContent();
                return;
            case 'article':
                html = await loadArticleContent(type);
                break;
            case 'category':
            case 'source':
                html = await loadCategoryOrSource(page, type);
                break;
            default:
                await loadMainContent();
                return;
        }
        
        contentContainer.innerHTML = html;
    } catch (error) {
        console.error(`Ошибка загрузки ${page}:`, error);
        showError('Ошибка загрузки страницы');
    }
}

// Загрузка результатов поиска
async function loadSearchResults(query) {
    const contentContainer = document.getElementById('dynamic-content');
    contentContainer.innerHTML = '<div class="loading">Поиск...</div>';

    try {
        const results = await fetch(`/api/search?query=${encodeURIComponent(query)}`)
            .then(res => res.json());

        renderSearchResults(query, results);
    } catch (error) {
        console.error('Ошибка поиска:', error);
        showError('Ошибка при выполнении поиска');
    }
}

// Рендер результатов поиска
function renderSearchResults(query, results) {
    const contentContainer = document.getElementById('dynamic-content');
    
    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('ru-RU');
    };

    contentContainer.innerHTML = `
        <div class="search-results">
            <h2>Результаты поиска: "${query}"</h2>
            ${results.length > 0 ? `
                <div class="results-list">
                    ${results.map(article => `
                        <div class="result-item">
                            <h3><a href="#" data-page="article" data-type="${article._id}">${article.title}</a></h3>
                            <p>${article.summary || 'Нет описания'}</p>
                            <div class="meta">
                                <span>${article.source}</span>
                                <span>${formatDate(article.publication_date)}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            ` : `
                <div class="no-results">
                    По вашему запросу ничего не найдено
                </div>
            `}
        </div>
    `;
}

// Показать ошибку
function showError(message) {
    const errorEl = document.createElement('div');
    errorEl.className = 'error-message';
    errorEl.textContent = message;
    document.body.appendChild(errorEl);
    setTimeout(() => errorEl.remove(), 5000);
}

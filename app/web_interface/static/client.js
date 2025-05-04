// Глобальное состояние приложения
const appState = {
    currentPage: 'main',
    currentType: null,
    articles: [],
    categories: [],
    sources: []
};

// Инициализация приложения
document.addEventListener("DOMContentLoaded", function() {
    initApp();
});

async function initApp() {
    setCurrentDate();
    setupNavigation();
    await loadInitialData();
    loadPage(getCurrentPage());
    setupEventListeners();
}

// Загрузка начальных данных
async function loadInitialData() {
    try {
        const [articlesRes, categoriesRes, sourcesRes] = await Promise.all([
            fetch('/api/latest-news'),
            fetch('/api/categories'),
            fetch('/api/sources')
        ]);
        
        appState.articles = await articlesRes.json();
        appState.categories = await categoriesRes.json();
        appState.sources = await sourcesRes.json();
        
    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
        showError('Не удалось загрузить данные. Пожалуйста, обновите страницу.');
    }
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
        year: 'numeric' 
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
            navigateTo(page, type);
        });
    });
    
    window.addEventListener('popstate', function(e) {
        loadPage(e.state || getCurrentPage());
    });
}

// Навигация между страницами
function navigateTo(page, type = null) {
    appState.currentPage = page;
    appState.currentType = type;
    
    history.pushState({ page, type }, '', 
        type ? `?page=${page}&type=${type}` : `?page=${page}`);
    
    loadPage({ page, type });
}

// Получение текущей страницы из URL
function getCurrentPage() {
    const params = new URLSearchParams(window.location.search);
    return {
        page: params.get('page') || 'main',
        type: params.get('type') || null
    };
}

// Загрузка страницы
async function loadPage({ page, type }) {
    const contentContainer = document.getElementById('dynamic-content');
    if (!contentContainer) return;
    
    showLoading();
    
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
            default:
                await loadMainPage(contentContainer);
        }
    } catch (error) {
        console.error(`Ошибка загрузки страницы ${page}:`, error);
        showError(`Не удалось загрузить страницу: ${page}`);
    } finally {
        hideLoading();
    }
}

// Пример реализации loadMainPage (остальные аналогично)
async function loadMainPage(container) {
    const topArticles = await fetch('/api/top-articles').then(res => res.json());
    const latestNews = await fetch('/api/latest-news').then(res => res.json());
    
    container.innerHTML = `
        <section class="digest">
            <h2>Новости дня</h2>
            <ul>
                ${topArticles.map(article => `
                    <li><a href="#" data-article="${article._id}">${article.title}</a></li>
                `).join('')}
            </ul>
        </section>
        <section class="latest-news">
            <h2>Последние новости</h2>
            ${latestNews.map(article => `
                <div class="news-item">
                    <img src="${article.image || 'placeholder.jpg'}" alt="${article.title}">
                    <div class="news-text">
                        <a href="#" data-article="${article._id}" class="news-title">${article.title}</a>
                        <p>${article.summary || 'Нет описания'}</p>
                    </div>
                </div>
            `).join('')}
        </section>
    `;
}

// Вспомогательные функции
function showLoading() {
    const loader = document.getElementById('loader') || createLoader();
    loader.style.display = 'block';
}

function hideLoading() {
    const loader = document.getElementById('loader');
    if (loader) loader.style.display = 'none';
}

function createLoader() {
    const loader = document.createElement('div');
    loader.id = 'loader';
    loader.innerHTML = '<div class="spinner"></div>';
    document.body.appendChild(loader);
    return loader;
}

function showError(message) {
    const errorEl = document.createElement('div');
    errorEl.className = 'error-message';
    errorEl.textContent = message;
    document.body.appendChild(errorEl);
    setTimeout(() => errorEl.remove(), 5000);
}

// Настройка обработчиков событий
function setupEventListeners() {
    // Обработка кликов по статьям
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-article]')) {
            e.preventDefault();
            const articleId = e.target.getAttribute('data-article');
            navigateTo('article', articleId);
        }
    });

    // Поиск
    const searchInput = document.querySelector('.search-input');
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
}

// Функция поиска
async function performSearch(query) {
    try {
        const response = await fetch(`/api/search?query=${encodeURIComponent(query)}`);
        const results = await response.json();
        
        sessionStorage.setItem('searchResults', JSON.stringify({ query, results }));
        navigateTo('search');
        
    } catch (error) {
        console.error('Ошибка поиска:', error);
        showError('Ошибка при выполнении поиска');
    }
}

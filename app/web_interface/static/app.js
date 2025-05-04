// Добавляем функции для работы с MongoDB
async function connectToMongoDB() {
    try {
        // Подключение к MongoDB через SSH туннель (в реальном коде нужно использовать бэкенд)
        const response = await fetch('/api/mongodb/connect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ssh_host: '78.36.44.126',
                ssh_port: 57381,
                ssh_user: 'server',
                ssh_password: 'tppo'
            })
        });
        
        if (!response.ok) {
            throw new Error('Connection failed');
        }
        
        return await response.json();
    } catch (error) {
        console.error('MongoDB connection error:', error);
        return null;
    }
}

async function fetchArticles(category = null, source = null) {
    try {
        let url = '/api/mongodb/articles';
        const params = new URLSearchParams();
        
        if (category) params.append('category', category);
        if (source) params.append('source', source);
        
        if (params.toString()) {
            url += `?${params.toString()}`;
        }
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('Failed to fetch articles');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching articles:', error);
        return [];
    }
}

async function fetchDailyDigest() {
    try {
        const response = await fetch('/api/mongodb/daily-digest');
        if (!response.ok) {
            throw new Error('Failed to fetch daily digest');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching daily digest:', error);
        return { top_articles: [] };
    }
}

async function fetchArticleById(id) {
    try {
        const response = await fetch(`/api/mongodb/articles/${id}`);
        if (!response.ok) {
            throw new Error('Failed to fetch article');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching article:', error);
        return null;
    }
}

// Модифицируем существующие функции для работы с MongoDB
async function loadMainPage(container) {
    // Получаем топовые статьи за день
    const digest = await fetchDailyDigest();
    const topArticles = digest.top_articles || [];
    
    // Получаем последние новости
    const latestNews = await fetchArticles();
    
    // Формируем HTML для дайджеста
    let digestHTML = `
        <section class="digest">
            <h2>Новости дня</h2>
            <ul>
    `;
    
    topArticles.slice(0, 3).forEach(article => {
        digestHTML += `<li><a href="#" data-article="${article._id}">${article.title}</a></li>`;
    });
    
    digestHTML += `
            </ul>
        </section>
        <section class="latest-news">
            <h2>Последние новости</h2>
    `;
    
    latestNews.slice(0, 2).forEach(article => {
        digestHTML += `
            <div class="news-item">
                <img src="${article.image || 'foto.jpg'}" alt="">
                <div class="news-text">
                    <a href="#" data-article="${article._id}" class="news-title">${article.title}</a>
                    <p>${article.summary || 'Описание новости'}</p>
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

    // Получаем статьи по категории
    const currentNews = await fetchArticles(category);
    const categoryName = categoryNames[category] || "Категория";

    let digestHTML = `
        <section class="digest">
            <h2>Новости дня</h2>
            <ul>
    `;
    
    currentNews.slice(0, 3).forEach(news => {
        digestHTML += `<li><a href="#" data-article="${news._id}">${news.title}</a></li>`;
    });
    
    digestHTML += `
            </ul>
        </section>
        <section class="latest-news">
            <h2>Новости: ${categoryName}</h2>
    `;
    
    currentNews.forEach(news => {
        digestHTML += `
            <div class="news-item">
                <img src="${news.image || 'foto.jpg'}" alt="">
                <div class="news-text">
                    <a href="#" data-article="${news._id}" class="news-title">${news.title}</a>
                    <p>${news.summary || 'Описание новости'}</p>
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
        "reviews": "Отзывы",
        "stat": "Статистические отчеты"
    };

    // Получаем статьи по источнику
    const currentNews = await fetchArticles(null, source);
    const sourceName = sourceNames[source] || "Источник";

    let html = `
        <section class="digest">
            <h2>Новости дня</h2>
            <ul>
    `;
    
    currentNews.slice(0, 3).forEach(news => {
        html += `<li><a href="#" data-article="${news._id}">${news.title}</a></li>`;
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
                <img src="${news.image || 'foto.jpg'}" alt="">
                <div class="news-text">
                    <a href="#" data-article="${news._id}" class="news-title">${news.title}</a>
                    <p>${news.summary || 'Описание новости'}</p>
                    <small>Источник: ${news.source || 'Неизвестно'}</small>
                </div>
            </div>
        `;
    });
    
    html += `</section>`;
    container.innerHTML = html;
}

async function loadArticle(articleId) {
    // Получаем статью по ID
    const article = await fetchArticleById(articleId);
    
    if (!article) {
        article = {
            title: "Статья не найдена",
            content: "<p>Извините, запрошенная статья не найдена.</p>",
            image: "foto.jpg"
        };
    }
    
    const contentContainer = document.getElementById('dynamic-content');
    
    history.pushState({ page: 'article', type: articleId }, '', `?page=article&id=${articleId}`);
    
    contentContainer.innerHTML = `
        <div class="news-article">
            <div class="article-text">
                <h2 class="headline">${article.title}</h2>
                <p class="article-meta">
                    <span class="source">${article.source || 'Неизвестный источник'}</span>
                    <span class="date">${new Date(article.publication_date).toLocaleDateString()}</span>
                </p>
                ${article.text || article.content || '<p>Содержимое статьи отсутствует.</p>'}
            </div>
            <div class="article-image">
                <img src="${article.image || 'foto.jpg'}" alt="Фотография новости">
            </div>
        </div>
    `;
}

async function loadSearchResultsPage(container, query) {
    try {
        const response = await fetch(`/api/mongodb/search?query=${encodeURIComponent(query)}`);
        const searchData = await response.json();
        
        let html = `
            <div class="search-results-container">
                <h2 class="search-title">Результаты поиска: "${query}"</h2>
                <div class="results-count">Найдено статей: ${searchData.results.length}</div>
        `;

        if (searchData.results.length > 0) {
            html += '<div class="results-list">';
            searchData.results.forEach(item => {
                html += `
                    <div class="search-item">
                        <a href="#" data-article="${item._id}" class="search-item-title">${item.title}</a>
                        <p class="search-item-desc">${item.summary || 'Описание отсутствует'}</p>
                    </div>
                `;
            });
            html += '</div>';
        } else {
            html += `
                <div class="no-results">
                    <p>По запросу "${query}" ничего не найдено.</p>
                    <p>Попробуйте изменить формулировку запроса.</p>
                </div>
            `;
        }

        html += '</div>';
        container.innerHTML = html;
    } catch (error) {
        console.error('Search error:', error);
        container.innerHTML = `
            <div class="search-error">
                <p>Произошла ошибка при выполнении поиска.</p>
            </div>
        `;
    }
}

// Модифицируем loadPage для поддержки async/await
async function loadPage({ page, type, query }) {
    const contentContainer = document.getElementById('dynamic-content');
    
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
        console.error('Page loading error:', error);
        contentContainer.innerHTML = `
            <div class="error-message">
                <p>Произошла ошибка при загрузке страницы.</p>
            </div>
        `;
    }
}

// Остальные функции (setCurrentDate, setupNavigation, getCurrentPage и т.д.) остаются без изменений
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
    });

    // Инициализация поиска после полной загрузки DOM
    setTimeout(() => {
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
    }, 100);
});

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
            
            // Изменяем URL без перезагрузки
            const url = type ? `?page=${page}&type=${type}` : `?page=${page}`;
            history.pushState({ page, type }, '', url);
            
            // Загружаем страницу
            loadPage({ page, type });
        });
    });
    
    // Обработка кнопки "назад"
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
        type: params.get('type') || null
    };
}

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

function loadPage({ page, type }) {
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
        default:
            loadMainPage(contentContainer);
    }
}

function loadMainPage(container) {
    container.innerHTML = `
        <section class="digest">
            <h2>Новости дня</h2>
            <ul>
                <li><a href="#" data-article="1">Заголовок новости</a></li>
                <li><a href="#" data-article="2">Заголовок новости</a></li>
                <li><a href="#" data-article="3">Заголовок новости</a></li>
            </ul>
        </section>
        <section class="latest-news">
            <h2>Последние новости</h2>
            <div class="news-item">
                <img src="foto.jpg" alt="">
                <div class="news-text">
                    <a href="#" data-article="1" class="news-title">Заголовок новости</a>
                    <p>Это описание первой новости. Здесь можно рассказать подробнее о событии, которое произошло.</p>
                </div>
            </div>
            <div class="news-item">
                <img src="foto.jpg" alt="">
                <div class="news-text">
                    <a href="#" data-article="2" class="news-title">Заголовок новости</a>
                    <p>Это описание второй новости. Подробности о том, что произошло, можно добавить здесь.</p>
                </div>
            </div>
        </section>
    `;
}

function loadCategoryPage(container, category) {
    const categoryNames = {
        "culture": "Культура",
        "sports": "Спорт",
        "tech": "Технологии",
        "holidays": "Праздники",
        "education": "Образование"
    };

    const newsData = {
        "culture": [
            { id: 1, img: "foto.jpg", title: "Культурное событие", description: "Описание культурного события." },
            { id: 2, img: "foto.jpg", title: "Открытие выставки", description: "Подробности об открытии выставки." }
        ],
        "sports": [
            { id: 3, img: "foto.jpg", title: "Спортивный турнир", description: "Информация о спортивном турнире." },
            { id: 4, img: "foto.jpg", title: "Футбольный матч", description: "Результаты и обзор футбольного матча." }
        ],
        "tech": [
            { id: 5, img: "foto.jpg", title: "Технологическое открытие", description: "Информация о технологическом открытии." }
        ]
    };

    const currentNews = newsData[category] || [];
    const categoryName = categoryNames[category] || "Категория";

    let digestHTML = `
        <section class="digest">
            <h2>Новости дня</h2>
            <ul>
    `;

    currentNews.slice(0, 3).forEach(news => {
        digestHTML += `<li><a href="#" data-article="${news.id}">${news.title}</a></li>`;
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
                <img src="${news.img}" alt="">
                <div class="news-text">
                    <a href="#" data-article="${news.id}" class="news-title">${news.title}</a>
                    <p>${news.description}</p>
                </div>
            </div>
        `;
    });

    digestHTML += `</section>`;
    container.innerHTML = digestHTML;
}

function loadSourcePage(container, source) {
    const sourceNames = {
        "news": "Новостные сайты",
        "social": "Социальные сети",
        "reviews": "Отзывы",
        "stat": "Статистические отчеты"
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

function loadArticle(articleId) {
    const articles = {
        "1": {
            title: "Заголовок новости",
            content: `
                <p>In January 2021, a facial recognition system helped detain a man who had been on the federal wanted list for 8 years.
                   The suspect was found in a shopping mall and was immediately detained by the police.</p>
                <p>In March 2021, a facial recognition system helped detain a married couple who had been on the federal wanted list for 17 years.
                   They were located at a public transportation hub and taken into custody.</p>
                <p>In April 2022, a facial recognition system helped detain a man who had been on the federal wanted list for 13 years.
                   Law enforcement officers confirmed his identity through biometric scanning.</p>
            `,
            image: "foto.jpg"
        },
        "2": {
            title: "Другая важная новость",
            content: `
                <p>Это содержимое второй новости. Здесь может быть подробное описание события.</p>
                <p>Дополнительные детали и информация о происшествии.</p>
            `,
            image: "foto.jpg"
        }
    };

    const article = articles[articleId] || articles["1"];
    const contentContainer = document.getElementById('dynamic-content');

    history.pushState({ page: 'article', type: articleId }, '', `?page=article&id=${articleId}`);

    contentContainer.innerHTML = `
        <div class="news-article">
            <div class="article-text">
                <h2 class="headline">${article.title}</h2>
                ${article.content}
            </div>
            <div class="article-image">
                <img src="${article.image}" alt="Фотография новости">
            </div>
        </div>
    `;
}

function loadArticlePage(container, articleId) {
    loadArticle(articleId);
}

// Демонстрационные данные для поиска
const demoArticles = [
    { id: 1, title: "Культурное событие в Петрозаводске", description: "В городе прошел фестиваль народного творчества", img: "foto.jpg" },
    { id: 2, title: "Спортивные новости", description: "Местная футбольная команда выиграла турнир", img: "foto.jpg" },
    { id: 3, title: "Технологии в образовании", description: "Школы Петрозаводска получают новое оборудование", img: "foto.jpg" },
    { id: 4, title: "Новый парк открыт", description: "В центре города открыли новый парк культуры и отдыха", img: "foto.jpg" }
];

function performSearch(query) {
    fetch(`http://localhost:8000/api/search?query=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            const results = data.map(item => ({
                id: item._id.$oid,  // из MongoDB ObjectId
                title: item.title,
                description: item.source || '',
                img: "foto.jpg", // если нет картинок в БД — можно оставить заглушку
                url: item.url
            }));

            sessionStorage.setItem('searchResults', JSON.stringify({
                query: query,
                results: results
            }));

            history.pushState({ page: 'search', query: query }, '', `?page=search&query=${encodeURIComponent(query)}`);
            loadPage({ page: 'search', query: query });
        })
        .catch(err => {
            console.error("Search error:", err);
        });
}

// Обновлённая функция loadPage
function loadPage({ page, type, query }) {
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

// Функция для отображения результатов поиска
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
                    <a href="#" data-article="${item.id}" class="search-item-title">${item.title}</a>
                    <p class="search-item-desc">${item.description}</p>
                </div>
            `;
        });
        html += '</div>';
    } else {
        html += `
            <div class="no-results">
                <p>По запросу "${searchData.query}" ничего не найдено.</p>
                <p>Попробуйте изменить формулировку запроса.</p>
            </div>
        `;
    }

    html += '</div>';
    container.innerHTML = html;
}

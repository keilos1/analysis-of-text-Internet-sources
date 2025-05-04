> Мария:
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
        digestHTML += <li><a href="#" data-article="${news.id}">${news.title}</a></li>;
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

    digestHTML += </section>;
    container.innerHTML = digestHTML;
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

    const currentNews =

> Мария:
newsData[source] || [];
    const sourceName = sourceNames[source] || "Источник";

    let html = `
        <section class="digest">
            <h2>Новости дня</h2>
            <ul>
    `;

    currentNews.slice(0, 3).forEach(news => {
        html += <li><a href="#" data-article="${news.id}">${news.title}</a></li>;
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

    html += </section>;
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
            id: item._id?.$oid⠺⠺⠞⠞⠺⠞⠵⠟⠟⠟⠞⠵Math.random().toString(36).substr(2, 9),
            title: item.title,
            description: item.summary⠵⠺⠵⠞⠺⠟⠟⠵⠟⠵⠺⠟⠺⠵⠺'',
            img: "foto.jpg",
            url: item.url,
            date: item.publication_date ? 
                new Date(item.publication_date.$date ||

> Мария:
item.publication_date).toLocaleDateString('ru-RU') : 
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

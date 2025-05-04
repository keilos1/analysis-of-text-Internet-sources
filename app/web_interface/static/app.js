const express = require('express');
const { MongoClient, ObjectId } = require('mongodb');
const cors = require('cors');
const app = express();
const port = 8000;

// Подключение к MongoDB
const uri = "mongodb://localhost:27017";
const client = new MongoClient(uri);

async function connectDB() {
    try {
        await client.connect();
        console.log("Connected to MongoDB");
        return client.db('newsDB');
    } catch (e) {
        console.error("Connection to MongoDB failed", e);
        throw e;
    }
}

// Middleware
app.use(cors());
app.use(express.json());

// API для топовых новостей
app.get('/api/top-articles', async (req, res) => {
    try {
        const db = await connectDB();
        const digestCollection = db.collection('daily_digest');
        const articlesCollection = db.collection('articles');
        
        // Получаем последнюю сводку дня
        const latestDigest = await digestCollection.findOne({}, { sort: { date: -1 } });
        
        if (!latestDigest) {
            return res.status(404).json({ error: "No digest found" });
        }
        
        // Преобразуем ObjectId для запроса
        const topArticlesIds = latestDigest.top_articles.map(id => new ObjectId(id));
        
        // Получаем топовые статьи из сводки
        const topArticles = await articlesCollection.find({ 
            _id: { $in: topArticlesIds } 
        }).toArray();
        
        res.json(topArticles);
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: "Internal server error" });
    }
});

// API для последних новостей
app.get('/api/latest-news', async (req, res) => {
    try {
        const db = await connectDB();
        const articlesCollection = db.collection('articles');
        
        // Получаем 10 последних новостей
        const latestNews = await articlesCollection.find()
            .sort({ publication_date: -1 })
            .limit(10)
            .toArray();
            
        res.json(latestNews);
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: "Internal server error" });
    }
});

// API для получения статьи по ID
app.get('/api/article/:id', async (req, res) => {
    try {
        const db = await connectDB();
        const articlesCollection = db.collection('articles');
        
        const article = await articlesCollection.findOne({ 
            _id: new ObjectId(req.params.id) 
        });
        
        if (!article) {
            return res.status(404).json({ error: "Article not found" });
        }
        
        res.json(article);
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: "Internal server error" });
    }
});

// API для поиска
app.get('/api/search', async (req, res) => {
    try {
        const query = req.query.query;
        if (!query) {
            return res.status(400).json({ error: "Query parameter is required" });
        }
        
        const db = await connectDB();
        const articlesCollection = db.collection('articles');
        
        // Создаем текстовый индекс (делается один раз)
        // await articlesCollection.createIndex({ title: "text", summary: "text" });
        
        const results = await articlesCollection.find({
            $text: { $search: query }
        }).toArray();
        
        res.json(results);
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: "Internal server error" });
    }
});

// API для новостей по категории
app.get('/api/category/:category', async (req, res) => {
    try {
        const category = req.params.category;
        const db = await connectDB();
        const articlesCollection = db.collection('articles');
        
        const articles = await articlesCollection.find({
            category: category
        }).sort({ publication_date: -1 }).limit(10).toArray();
        
        res.json(articles);
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: "Internal server error" });
    }
});

// API для новостей по источнику
app.get('/api/source/:source', async (req, res) => {
    try {
        const source = req.params.source;
        const db = await connectDB();
        const articlesCollection = db.collection('articles');
        
        const articles = await articlesCollection.find({
            source: source
        }).sort({ publication_date: -1 }).limit(10).toArray();
        
        res.json(articles);
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: "Internal server error" });
    }
});

// API для списка источников
app.get('/api/sources', async (req, res) => {
    try {
        const db = await connectDB();
        const sourcesCollection = db.collection('sources');
        
        const sources = await sourcesCollection.find().toArray();
        res.json(sources);
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: "Internal server error" });
    }
});

// API для списка категорий
app.get('/api/categories', async (req, res) => {
    try {
        const db = await connectDB();
        const articlesCollection = db.collection('articles');
        
        const categories = await articlesCollection.distinct("category");
        res.json(categories);
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: "Internal server error" });
    }
});

// Запуск сервера
app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});

// Функция для периодического обновления данных
async function updateNewsData() {
    try {
        const db = await connectDB();
        const articlesCollection = db.collection('articles');
        const sourcesCollection = db.collection('sources');
        
        // Обновляем last_checked для источников
        await sourcesCollection.updateMany({}, {
            $set: { last_checked: new Date() }
        });
        
        console.log('News data updated at', new Date());
    } catch (e) {
        console.error('Error updating news data:', e);
    }
}

// Обновляем данные каждые 30 минут
setInterval(updateNewsData, 30 * 60 * 1000);
updateNewsData(); // Первое обновление при запуске

// Graceful shutdown
process.on('SIGINT', async () => {
    await client.close();
    process.exit();
});

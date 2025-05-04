require('dotenv').config();
const express = require('express');
const { MongoClient, ObjectId } = require('mongodb');
const cors = require('cors');
const path = require('path');

const app = express();
const port = process.env.PORT || 8000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Подключение к MongoDB
const client = new MongoClient(process.env.MONGODB_URI || 'mongodb://localhost:27017');

async function connectDB() {
    try {
        await client.connect();
        return client.db(process.env.DB_NAME || 'newsDB');
    } catch (err) {
        console.error('MongoDB connection error:', err);
        process.exit(1);
    }
}

// API endpoints
app.get('/api/top-articles', async (req, res) => {
    try {
        const db = await connectDB();
        const digest = await db.collection('daily_digest')
            .findOne({}, { sort: { date: -1 } });
        
        const articles = await db.collection('articles')
            .find({ _id: { $in: digest.top_articles.map(id => new ObjectId(id)) } })
            .toArray();
            
        res.json(articles);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.get('/api/latest-news', async (req, res) => {
    try {
        const db = await connectDB();
        const articles = await db.collection('articles')
            .find()
            .sort({ publication_date: -1 })
            .limit(10)
            .toArray();
            
        res.json(articles);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.get('/api/article/:id', async (req, res) => {
    try {
        const db = await connectDB();
        const article = await db.collection('articles')
            .findOne({ _id: new ObjectId(req.params.id) });
            
        if (!article) {
            return res.status(404).json({ error: 'Article not found' });
        }
        
        res.json(article);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.get('/api/search', async (req, res) => {
    try {
        const query = req.query.query;
        if (!query) {
            return res.status(400).json({ error: 'Query parameter is required' });
        }

        const db = await connectDB();
        const articles = await db.collection('articles')
            .find({ $text: { $search: query } })
            .toArray();
            
        res.json(articles);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Запуск сервера
async function startServer() {
    await connectDB();
    app.listen(port, () => {
        console.log(`Server running on port ${port}`);
    });
}

startServer();

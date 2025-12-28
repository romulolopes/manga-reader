const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

const app = express();
const PORT = 3000;
const SECRET_KEY = 'manga_reader_secret_key_change_me';

app.use(cors());
app.use(bodyParser.json());

// Banco de dados em arquivo (cria automaticamente)
const db = new sqlite3.Database('./database.sqlite');

db.serialize(() => {
    db.run(`CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        last_link TEXT,
        last_page INTEGER
    )`);
});

// --- ROTAS ---

// Registro
app.post('/register', (req, res) => {
    const { username, password } = req.body;
    if(!username || !password) return res.status(400).send("Faltam dados.");
    
    const hashedPassword = bcrypt.hashSync(password, 8);

    db.run(`INSERT INTO users (username, password) VALUES (?, ?)`, 
        [username, hashedPassword], 
        function(err) {
            if (err) return res.status(500).json({ error: "Usuário já existe ou erro no servidor." });
            res.status(200).json({ message: "Usuário criado com sucesso!" });
        }
    );
});

// Login
app.post('/login', (req, res) => {
    const { username, password } = req.body;

    db.get(`SELECT * FROM users WHERE username = ?`, [username], (err, user) => {
        if (err || !user) return res.status(404).json({ error: "Usuário não encontrado." });

        const passwordIsValid = bcrypt.compareSync(password, user.password);
        if (!passwordIsValid) return res.status(401).json({ error: "Senha inválida." });

        const token = jwt.sign({ id: user.id }, SECRET_KEY, { expiresIn: 86400 }); // 24h

        res.status(200).json({
            auth: true,
            token: token,
            username: user.username,
            lastLink: user.last_link,
            lastPage: user.last_page
        });
    });
});

// Salvar Progresso
app.post('/save', (req, res) => {
    const token = req.headers['x-access-token'];
    if (!token) return res.status(401).send({ auth: false, message: 'No token provided.' });

    jwt.verify(token, SECRET_KEY, (err, decoded) => {
        if (err) return res.status(500).send({ auth: false, message: 'Token invalido.' });

        const { link, page } = req.body;
        db.run(`UPDATE users SET last_link = ?, last_page = ? WHERE id = ?`, 
            [link, page, decoded.id], 
            function(err) {
                if(err) return res.status(500).send("Erro ao salvar");
                res.status(200).send("Salvo");
            }
        );
    });
});

app.listen(PORT, () => {
    console.log(`Servidor rodando na porta ${PORT}`);
});
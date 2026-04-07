// login.js — Handles user authentication using PostgreSQL
// This example uses Node.js + Express + pg
// Make sure to: npm install express pg bcrypt jsonwebtoken cors

import express from 'express';
import pg from 'pg';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import cors from 'cors';

const app = express();
app.use(express.json());
app.use(cors());

// PostgreSQL connection
const pool = new pg.Pool({
  user: 'postgres',       // change
  host: 'localhost',      // change
  database: 'zaikax',     // change
  password: 'yourpassword', // change
  port: 5432
});

const JWT_SECRET = "REPLACE_WITH_SECRET_KEY";

// -------------------- REGISTER ------------------------
app.post('/register', async (req, res) => {
  const { name, email, password } = req.body;
  try {
    const hashed = await bcrypt.hash(password, 10);
    const checkUser = await pool.query("SELECT * FROM users WHERE email=$1", [email]);
    if (checkUser.rows.length > 0) return res.status(400).json({ error: "Email already exists" });

    await pool.query(
      "INSERT INTO users (name, email, password) VALUES ($1,$2,$3)",
      [name, email, hashed]
    );
    res.json({ message: "User registered successfully" });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Server error" });
  }
});

// -------------------- LOGIN ------------------------
app.post('/login', async (req, res) => {
  const { email, password } = req.body;
  try {
    const user = await pool.query("SELECT * FROM users WHERE email=$1", [email]);
    if (user.rows.length === 0) return res.status(400).json({ error: "Invalid email or password" });

    const valid = await bcrypt.compare(password, user.rows[0].password);
    if (!valid) return res.status(400).json({ error: "Invalid email or password" });

    const token = jwt.sign({ id: user.rows[0].id, email: user.rows[0].email }, JWT_SECRET, { expiresIn: "7d" });
    res.json({ message: "Login success", token });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Server error" });
  }
});

// -------------------- AUTH MIDDLEWARE ------------------------
function auth(req, res, next) {
  const token = req.headers.authorization?.split(" ")[1];
  if (!token) return res.status(401).json({ error: "No token provided" });

  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded;
    next();
  } catch {
    res.status(401).json({ error: "Invalid token" });
  }
}

// -------------------- PROFILE ROUTE ------------------------
app.get('/profile', auth, async (req, res) => {
  try {
    const user = await pool.query("SELECT id, name, email FROM users WHERE id=$1", [req.user.id]);
    res.json(user.rows[0]);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Server error" });
  }
});

// -------------------- START SERVER ------------------------
app.listen(4000, () => console.log('Auth server running on port 4000'));
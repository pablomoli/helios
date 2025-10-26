require('dotenv').config();
const express = require('express');
const cors = require('cors');
const routes = require('./controllers');

const app = express();
const PORT = process.env.PORT || 5000;

// Enable CORS so React frontend can call the API
app.use(cors());

// Parse incoming JSON and URL-encoded payloads
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Use the routes defined in the 'controllers' directory
app.use('/api', routes); // prefix all routes with /api

// Start the server
app.listen(PORT, () => {
  console.log(`✅ Server running on port ${PORT}`);
});

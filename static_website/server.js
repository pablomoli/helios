require('dotenv').config();
const express = require('express');
const path = require('path');
const routes = require('./controllers');
const { engine } = require('express-handlebars');

const app = express();

// Set Handlebars as the view engine
app.engine('handlebars', engine());
app.set('view engine', 'handlebars');
app.set('views', path.join(__dirname, 'views'));

const PORT = process.env.PORT || 3004;

// Serve static files from the 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

// --- MISSING BODY PARSERS ---
app.use(express.json()); // for parsing application/json
app.use(express.urlencoded({ extended: true })); // for parsing form submissions

// Use the routes defined in the 'controllers' directory
app.use(routes);

// Start the server
app.listen(PORT, () => {
  console.log('Now listening on port', PORT);
});

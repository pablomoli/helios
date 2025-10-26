const express = require('express');
const homeRouter = require('./home');
const snowflakeRouter = require('./snowflake');

const router = express.Router();

// Home route (example API endpoint)
router.use('/', homeRouter);

// Snowflake routes
router.use('/snowflake', snowflakeRouter);

module.exports = router;

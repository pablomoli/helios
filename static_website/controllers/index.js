// routes/index.js (or wherever your main router is)

const express = require('express');
const homeRouter = require('./home');
const snowflakeRouter = require('./snowflake');

const router = express.Router();

router.use('/', homeRouter);

router.use('/snowflake', snowflakeRouter);

module.exports = router;

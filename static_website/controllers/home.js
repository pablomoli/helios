const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
    console.log('Serving Home Page');
    res.render('chat', { name: 'Stranger', title: 'Hello Page' });
});

module.exports = router;

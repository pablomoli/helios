const express = require('express');
const router = express.Router();

// Example API endpoint for the home page
router.get('/', (req, res) => {
    console.log('Serving Home API');
    res.json({
        message: 'Welcome to Helios AI!',
        user: 'Stranger',
        info: 'This is the home API endpoint'
    });
});

module.exports = router;

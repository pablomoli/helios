// routes/snowflake.js

const express = require('express');
const router = express.Router();
const fetch = require('node-fetch'); // NOTE: Optional on Node 18+

// --- SECURE CONFIGURATION (Fetch from Environment Variables) ---
const ACCOUNT_IDENTIFIER = process.env.SNOWFLAKE_ACCOUNT_IDENTIFIER;
const SNOWFLAKE_TOKEN = process.env.PERSONAL_ACCESS_TOKEN;

// Dynamically construct the full URL using the environment variable
const SNOWFLAKE_URL = `https://${ACCOUNT_IDENTIFIER}.snowflakecomputing.com/api/v2/cortex/inference:complete`;
// ----------------------------------------------------------------

router.post('/complete', async (req, res) => {
    console.log("/complete --test");

    if (!SNOWFLAKE_TOKEN || !ACCOUNT_IDENTIFIER) {
        console.error("Missing SNOWFLAKE_BEARER_TOKEN or SNOWFLAKE_ACCOUNT_IDENTIFIER in environment.");
        return res.status(500).json({ error: "Server configuration error: Missing required keys." });
    }

    const userMessage = req.body.message;
    if (!userMessage) {
        return res.status(400).json({ error: "Message content is required." });
    }

    try {
        // --- 0. Get public IP ---
        const ipResponse = await fetch('https://icanhazip.com');
        const publicIP = (await ipResponse.text()).trim();
        console.log('Server public IP:', publicIP);

        // --- 1. Construct the request body for Snowflake ---
        const payload = {
            model: "claude-3-5-sonnet",
            messages: [{ role: "user", content: userMessage }]
        };

        // --- 2. Make the API call to Snowflake ---
        const response = await fetch(SNOWFLAKE_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${SNOWFLAKE_TOKEN}`
            },
            body: JSON.stringify(payload)
        });

        const responseText = await response.text();
        const lines = responseText.split('\n').filter(l => l.startsWith('data: '));

        let finalText = '';
        for (const line of lines) {
            try {
                const json = JSON.parse(line.replace(/^data: /, ''));
                const content = json.choices?.[0]?.delta?.content || '';
                finalText += content;
            } catch (e) {
                console.error("Failed to parse chunk:", e);
            }
        }

        res.json({ botResponse: finalText, publicIP });


    } catch (error) {
        console.error("Error calling Snowflake Cortex API:", error.message);
        res.status(500).json({ error: "Failed to get a response from the AI assistant." });
    }
});


module.exports = router;

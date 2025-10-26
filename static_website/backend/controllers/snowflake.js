const express = require('express');
const router = express.Router();
const fetch = require('node-fetch'); // Optional on Node 18+

// --- SECURE CONFIGURATION (Environment Variables) ---
const ACCOUNT_IDENTIFIER = process.env.SNOWFLAKE_ACCOUNT_IDENTIFIER;
const SNOWFLAKE_TOKEN = process.env.PERSONAL_ACCESS_TOKEN;

const SNOWFLAKE_URL = `https://${ACCOUNT_IDENTIFIER}.snowflakecomputing.com/api/v2/cortex/inference:complete`;
// ----------------------------------------------------------------

router.post('/complete', async (req, res) => {
    console.log('[Snowflake] /complete called');

    if (!SNOWFLAKE_TOKEN || !ACCOUNT_IDENTIFIER) {
        console.error("[Snowflake] Missing required environment keys");
        return res.status(500).json({ error: "Server configuration error: Missing required keys." });
    }

    const userMessage = req.body.message;
    if (!userMessage) {
        return res.status(400).json({ error: "Message content is required." });
    }

    try {
        // --- 0. Get server public IP ---
        const ipResponse = await fetch('https://icanhazip.com');
        const publicIP = (await ipResponse.text()).trim();
        console.log('[Snowflake] Server public IP:', publicIP);

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
        const lines = responseText.split('\n').filter(line => line.startsWith('data: '));

        let finalText = '';
        for (const line of lines) {
            try {
                const json = JSON.parse(line.replace(/^data: /, ''));
                const content = json.choices?.[0]?.delta?.content || '';
                finalText += content;
            } catch (err) {
                console.error('[Snowflake] Failed to parse chunk:', err);
            }
        }

        res.json({ botResponse: finalText, publicIP });

    } catch (error) {
        console.error('[Snowflake] Error calling Snowflake Cortex API:', error.message);
        res.status(500).json({ error: "Failed to get a response from the AI assistant." });
    }
});

module.exports = router;

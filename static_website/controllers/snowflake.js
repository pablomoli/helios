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
    // 1. Check for required environment variables and message
    if (!SNOWFLAKE_TOKEN || !ACCOUNT_IDENTIFIER) {
        console.error("Missing SNOWFLAKE_BEARER_TOKEN or SNOWFLAKE_ACCOUNT_IDENTIFIER in environment.");
        return res.status(500).json({ error: "Server configuration error: Missing required keys." });
    }

    const userMessage = req.body.message;

    if (!userMessage) {
        return res.status(400).json({ error: "Message content is required." });
    }

    try {
        // 2. Construct the request body for the Snowflake API
        const payload = {
            "model": "claude-3-5-sonnet",
            "messages": [
                {
                    "role": "user",
                    "content": userMessage
                }
            ]
        };

        // 3. Make the API call to Snowflake
        const response = await fetch(SNOWFLAKE_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // Use the PAT as the Bearer Token
                'Authorization': `Bearer ${SNOWFLAKE_TOKEN}`
            },
            body: JSON.stringify(payload)
        });

        // Check for HTTP errors
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Snowflake API Error: ${response.status} - ${errorText}`);
        }

        // 4. Parse the JSON response
        const data = await response.json();

        // 5. Extract the chatbot's response text
        const botResponse = data.choices[0].message.content;

        // 6. Send the chatbot's message back to the frontend
        res.json({ botResponse });

    } catch (error) {
        console.error("Error calling Snowflake Cortex API:", error.message);
        res.status(500).json({ error: "Failed to get a response from the AI assistant." });
    }
});

module.exports = router;

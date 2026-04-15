const fs = require('fs');
const https = require('https');

// --- CONFIGURATION ---
const ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzAwMzU5NzksInVzZXJfbmFtZSI6IjEiLCJhdXRob3JpdGllcyI6WyJST0xFX0REQVBQX1VTRVIiLCJST0xFX0REX1BVSkFfQ0FTSElFUiIsIlJPTEVfRERfUFVKQV9NQU5BR0VSIiwiUk9MRV9ESVZJTkVfRlJBTkNISVNFRV9DQVNISUVSIiwiUk9MRV9ERF9QVUpBX0FETUlOIiwiUk9MRV9EREFQUF9BRE1JTiIsIlJPTEVfRElWSU5FX0FETUlOIiwiUk9MRV9ESVZJTkVfRlJBTkNISVNFRV9PUEVSQVRPUiIsIlJPTEVfRElWSU5FX0ZSQU5DSElTRUVfQUNDT1VOVEFOVCIsIlJPTEVfRERBUFBfU1VQUE9SVCIsIlJPTEVfRElWSU5FX0ZSQU5DSElTRUVfTUFOQUdFUiIsIlJPTEVfRElWSU5FX0ZSQU5DSElTRUUiLCJST0xFX0REQVBQX0NPTlRFTlRfTUFOQUdFUiIsIlJPTEVfRERfUFVKQV9NT0RFUkFUT1IiXSwianRpIjoiTGgtR29hR2Y4SUtzVWZqZkwzel91VklONHVVIiwiY2xpZW50X2lkIjoidGVjaHhyIiwic2NvcGUiOlsiYWxsIl19.PTCnQH7arrry3I00LUl0ZIts217_S-xvromr3mtrkJOwjVvuQtPP3kdNurW5mrpc-gLtPwE9TXA5H-Uh_P7ly0zg926bwslDiW9k528T8mYlsshcqx9WHShISCfPq4wZaZ1L93rdE0v2bIgWiOe8NliFY6Sqw1nSIv_gsY82-j9B98LveZWTkBjaGx4Hg54vpFB6upmBU2u2OCTcwW1XTaWBxj1v2BcMScHUVkj9t-kqrAz25hZLWT6ksb3BsoyCTMjVvLuql-IxPuRA8ghKKw4V95qT1iTzO3KKpwkFlvboqMq4tb7HmlYufFDJpoi8E6ccD5feS66UkxYHDaikzQ";
const HOST = "devgateway.techxrdev.in";
const RESPONSE_FILE = "response.json";

// Set LIMIT to a number (e.g., 5) to test on a few cards.
// Set LIMIT to null to run for all cards.
const LIMIT = null;

// Set DRY_RUN to true to log without making real requests.
const DRY_RUN = false;
// ---------------------

function sendReorderRequest(cardId, episodeIds) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify(episodeIds);
        const options = {
            hostname: HOST,
            path: `/api/content/cms/cards/${cardId}/episodes/reorder`,
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${ACCESS_TOKEN}`,
                'Content-Length': Buffer.byteLength(data)
            }
        };

        if (DRY_RUN) {
            console.log(`[DRY RUN] Would PUT to ${HOST}${options.path}`);
            console.log(`[DRY RUN] Body: ${data}`);
            resolve({ status: 200, body: 'Dry run success' });
            return;
        }

        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                if (res.statusCode >= 200 && res.statusCode < 300) {
                    resolve({ status: res.statusCode, body });
                } else {
                    reject({ status: res.statusCode, body });
                }
            });
        });

        req.on('error', (e) => reject(e));
        req.write(data);
        req.end();
    });
}

async function main() {
    try {
        const rawData = fs.readFileSync(RESPONSE_FILE, 'utf8');
        const cards = JSON.parse(rawData);

        // Apply limit if specified
        const cardsToProcess = LIMIT ? cards.slice(0, LIMIT) : cards;

        console.log(`Processing ${cardsToProcess.length} cards...`);

        for (let i = 0; i < cardsToProcess.length; i++) {
            const card = cardsToProcess[i];
            const cardId = card.id;
            const episodeIds = card.episodes.map(ep => ep.id);

            if (episodeIds.length === 0) {
                console.log(`[${i + 1}/${cardsToProcess.length}] Skipping card ${cardId}: No episodes found.`);
                continue;
            }

            console.log(`[${i + 1}/${cardsToProcess.length}] Reordering episodes for card ${cardId}...`);

            try {
                const result = await sendReorderRequest(cardId, episodeIds);
                console.log(`   Successfully reordered card ${cardId}. Status: ${result.status}`);
            } catch (error) {
                console.error(`   Failed to reorder card ${cardId}. Status: ${error.status || 'Error'}`);
                console.error(`   Error Body: ${error.body || error.message}`);
            }

            // Small delay to prevent rate limiting
            if (!DRY_RUN) {
                await new Promise(resolve => setTimeout(resolve, 900));
            }
        }

        console.log("\nReordering process completed.");
    } catch (error) {
        console.error(`Critical Error: ${error.message}`);
    }
}

main();

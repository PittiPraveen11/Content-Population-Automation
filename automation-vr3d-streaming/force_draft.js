const https = require('https');

const API_BASE_URL = 'devgateway.techxrdev.in';
const API_PATH_PREFIX = '/api/content/cms/episodes/';
// Using the same token as in update_status_draft.js
const AUTH_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Njk3NzEyNjMsInVzZXJfbmFtZSI6IjEiLCJhdXRob3JpdGllcyI6WyJST0xFX0REQVBQX1VTRVIiLCJST0xFX0REX1BVSkFfQ0FTSElFUiIsIlJPTEVfRERfUFVKQV9NQU5BR0VSIiwiUk9MRV9ESVZJTkVfRlJBTkNISVNFRV9DQVNISUVSIiwiUk9MRV9ERF9QVUpBX0FETUlOIiwiUk9MRV9EREFQUF9BRE1JTiIsIlJPTEVfRElWSU5FX0FETUlOIiwiUk9MRV9ESVZJTkVfRlJBTkNISVNFRV9PUEVSQVRPUiIsIlJPTEVfRElWSU5FX0ZSQU5DSElTRUVfQUNDT1VOVEFOVCIsIlJPTEVfRERBUFBfU1VQUE9SVCIsIlJPTEVfRElWSU5FX0ZSQU5DSElTRUVfTUFOQUdFUiIsIlJPTEVfRElWSU5FX0ZSQU5DSElTRUUiLCJST0xFX0REQVBQX0NPTlRFTlRfTUFOQUdFUiIsIlJPTEVfRERfUFVKQV9NT0RFUkFUT1IiXSwianRpIjoiNWpQSFdocG1NSHYwOGx5SHFDZm5FVUtuTy1JIiwiY2xpZW50X2lkIjoidGVjaHhyIiwic2NvcGUiOlsiYWxsIl19.H75vwLkNH45bKNmsIMUQhGZAevuyNeg-dbp1O8pKW1qSl5gU-XV-viw7Un2YJT4VconyTmP4fA8FUjnteP30q747gXqgZRDAdzACY1TCXeqKR0ZyxEXPq95v5_OjSuwxpbZVYzV2gMfsxDEmav63HwI_N4QJCrrpt9glvDj5biHOQ77q9CIPmMRi5B2GIiw8hR9VVkuaY99jbh9uLhcVo0SaCgYvnc2D46h0s8x9KMqT_iRXLyQUnfxikgg_RTjouy5Z_g6ucsUW-38ObwSFYx0isIwrDE9oX5LeLky0OEI9q6wRMCREYwBg_hICMWq2ME9MQKZ9SBALecAGejJc6w";

const TARGET_IDS = [
    '693942fb64add5b2e7343ff2', // Shri Omkareshwar Shayan Shringar
    '6969c4f664add523f365dbac', // Shri Mahakaleshwar Darshan
    '6939430b64add5b2e7344036'  // Chitrakoot Darshan
];

function updateEpisodeStatus(episodeId) {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: API_BASE_URL,
            path: `${API_PATH_PREFIX}${episodeId}/goLiveStatus?status=DRAFT`,
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${AUTH_TOKEN}`
            }
        };

        console.log(`[REQ] PUT ${options.hostname}${options.path}`);

        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                console.log(`[RES] Status: ${res.statusCode}`);
                console.log(`[RES] Body: ${body}`);
                if (res.statusCode >= 200 && res.statusCode < 300) {
                    resolve({ status: res.statusCode, body: body });
                } else {
                    reject({ status: res.statusCode, body: body });
                }
            });
        });

        req.on('error', (e) => {
            console.error(`[ERR] Request Failed:`, e);
            reject(e);
        });

        req.end();
    });
}

async function main() {
    console.log("Starting Force Draft Update...");
    for (const id of TARGET_IDS) {
        console.log(`\nProcessing ID: ${id}`);
        try {
            await updateEpisodeStatus(id);
            console.log("-> Success");
        } catch (error) {
            console.error("-> Failed");
        }
    }
}

main();

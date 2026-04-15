const fs = require('fs');
const https = require('https');
const path = require('path');

// --- CONSTANTS ---
const DRY_RUN = false;
const API_BASE_URL = 'devgateway.techxrdev.in';
const API_PATH_PREFIX = '/api/content/cms/episodes/';
const AUTH_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Njk3NzEyNjMsInVzZXJfbmFtZSI6IjEiLCJhdXRob3JpdGllcyI6WyJST0xFX0REQVBQX1VTRVIiLCJST0xFX0REX1BVSkFfQ0FTSElFUiIsIlJPTEVfRERfUFVKQV9NQU5BR0VSIiwiUk9MRV9ESVZJTkVfRlJBTkNISVNFRV9DQVNISUVSIiwiUk9MRV9ERF9QVUpBX0FETUlOIiwiUk9MRV9EREFQUF9BRE1JTiIsIlJPTEVfRElWSU5FX0FETUlOIiwiUk9MRV9ESVZJTkVfRlJBTkNISVNFRV9PUEVSQVRPUiIsIlJPTEVfRElWSU5FX0ZSQU5DSElTRUVfQUNDT1VOVEFOVCIsIlJPTEVfRERBUFBfU1VQUE9SVCIsIlJPTEVfRElWSU5FX0ZSQU5DSElTRUVfTUFOQUdFUiIsIlJPTEVfRElWSU5FX0ZSQU5DSElTRUUiLCJST0xFX0REQVBQX0NPTlRFTlRfTUFOQUdFUiIsIlJPTEVfRERfUFVKQV9NT0RFUkFUT1IiXSwianRpIjoiNWpQSFdocG1NSHYwOGx5SHFDZm5FVUtuTy1JIiwiY2xpZW50X2lkIjoidGVjaHhyIiwic2NvcGUiOlsiYWxsIl19.H75vwLkNH45bKNmsIMUQhGZAevuyNeg-dbp1O8pKW1qSl5gU-XV-viw7Un2YJT4VconyTmP4fA8FUjnteP30q747gXqgZRDAdzACY1TCXeqKR0ZyxEXPq95v5_OjSuwxpbZVYzV2gMfsxDEmav63HwI_N4QJCrrpt9glvDj5biHOQ77q9CIPmMRi5B2GIiw8hR9VVkuaY99jbh9uLhcVo0SaCgYvnc2D46h0s8x9KMqT_iRXLyQUnfxikgg_RTjouy5Z_g6ucsUW-38ObwSFYx0isIwrDE9oX5LeLky0OEI9q6wRMCREYwBg_hICMWq2ME9MQKZ9SBALecAGejJc6w";

// File Paths
const VIDEO_THUMBNAILS_PATH = path.join(__dirname, 'VideoThumbnails.json');
const API_RESPONSE_PATH = path.join(__dirname, 'vr-3d-response.json');

// --- HELPER FUNCTIONS ---

function cleanString(str) {
    if (!str) return '';
    return str.trim().toLowerCase().replace(/[^a-z0-9]/g, '');
}

// Function to make HTTPS PUT Request
function updateEpisodeStatus(episodeId) {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: API_BASE_URL,
            // URL: /api/content/cms/episodes/{id}/goLiveStatus?status=DRAFT
            path: `${API_PATH_PREFIX}${episodeId}/goLiveStatus?status=DRAFT`,
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${AUTH_TOKEN}`
            }
        };

        if (DRY_RUN) {
            console.log(`[DRY RUN] Would update STATUS to DRAFT for Episode ${episodeId}`);
            resolve({ status: 200, message: 'Dry Run Success' });
            return;
        }

        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                if (res.statusCode >= 200 && res.statusCode < 300) {
                    resolve({ status: res.statusCode, body: body });
                } else {
                    reject({ status: res.statusCode, body: body });
                }
            });
        });

        req.on('error', (e) => {
            reject(e);
        });

        // No body
        req.end();
    });
}


async function main() {
    try {
        console.log("Loading data files...");
        let thumbnailsRaw = fs.readFileSync(VIDEO_THUMBNAILS_PATH, 'utf8');
        let apiResponseRaw = fs.readFileSync(API_RESPONSE_PATH, 'utf8');

        // Strip BOM
        thumbnailsRaw = thumbnailsRaw.replace(/^\uFEFF/, '');
        apiResponseRaw = apiResponseRaw.replace(/^\uFEFF/, '');

        const videoThumbnails = JSON.parse(thumbnailsRaw);

        if (apiResponseRaw.trim().startsWith('"cards"')) {
            apiResponseRaw = '{' + apiResponseRaw + '}';
        }
        const apiResponse = JSON.parse(apiResponseRaw);

        // Extract items
        let apiCards = [];
        if (apiResponse.data && Array.isArray(apiResponse.data.cards)) {
            apiCards = apiResponse.data.cards;
        } else if (apiResponse.cards && Array.isArray(apiResponse.cards)) {
            apiCards = apiResponse.cards;
        } else {
            apiCards = Array.isArray(apiResponse) ? apiResponse : [];
        }

        // Flatten episodes
        const allEpisodes = [];
        apiCards.forEach(card => {
            if (card.episodes && Array.isArray(card.episodes)) {
                card.episodes.forEach(ep => {
                    allEpisodes.push({
                        ...ep,
                        parentTitle: card.thumbnail?.title?.en || card.thumbnail?.title?.hi,
                        cardId: card.id
                    });
                });
            }
        });

        console.log("Checking for videos without Adaptive Streaming URL...");

        let matchCount = 0;
        let processedCount = 0;

        for (const key in videoThumbnails) {
            const vt = videoThumbnails[key];
            const url = vt.AdaptiveStreamingVideoURL;

            // USER REQUEST: "only search for AdaptiveStreamingVideoURL which ever json did not contain this"
            if (!url || url.trim() === "") {
                // This is a target for DRAFT status
                const targetTitle = cleanString(vt.videoTitle);

                // Find Episode ID (not Card ID)
                let matchedEpisode = allEpisodes.find(ep => {
                    const epTitle = cleanString(ep.thumbnail?.title?.en);
                    return epTitle === targetTitle;
                });

                if (matchedEpisode) {
                    console.log(`Found candidate for DRAFT: "${vt.videoTitle}" -> Episode ID: ${matchedEpisode.id}`);
                    matchCount++;

                    try {
                        await updateEpisodeStatus(matchedEpisode.id);
                        processedCount++;
                    } catch (error) {
                        console.error(`Failed to update status for ${vt.videoTitle}:`, error);
                    }

                } else {
                    console.warn(`Candidate "${vt.videoTitle}" NOT FOUND in API Response.`);
                }
            }
        }

        console.log(`\n--- SUMMARY ---`);
        console.log(`Total Candidates: ${matchCount}`);
        console.log(`Successfully Processed: ${processedCount}`);

    } catch (err) {
        console.error("Critical Error:", err);
    }
}

main();

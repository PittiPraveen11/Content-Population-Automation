const fs = require('fs');
const https = require('https');
const path = require('path');

// --- CONSTANTS ---
const DRY_RUN = false; // Set to false to actually execute API calls
const LIMIT_UPDATES = 100;
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
function updateStreamingOptions(episodeId, payload) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify(payload);

        const options = {
            hostname: API_BASE_URL,
            path: `${API_PATH_PREFIX}${episodeId}/streamingOptions`,
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${AUTH_TOKEN}`
            }
        };

        if (DRY_RUN) {
            console.log(`[DRY RUN] Would update Episode ${episodeId} with payload:`);
            console.log(JSON.stringify(payload, null, 2));
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

        req.write(data);
        req.end();
    });
}

// --- MAIN LOGIC ---

async function main() {
    try {
        console.log("Loading data files...");
        let thumbnailsRaw = fs.readFileSync(VIDEO_THUMBNAILS_PATH, 'utf8');
        let apiResponseRaw = fs.readFileSync(API_RESPONSE_PATH, 'utf8');

        // Strip BOM if present
        thumbnailsRaw = thumbnailsRaw.replace(/^\uFEFF/, '');
        apiResponseRaw = apiResponseRaw.replace(/^\uFEFF/, '');

        console.log("Thumbnails start:", thumbnailsRaw.substring(0, 50));
        console.log("API Response start:", apiResponseRaw.substring(0, 50));

        const videoThumbnails = JSON.parse(thumbnailsRaw);

        // Handle partial JSON in apiResponse (starts with "cards": ...)
        if (apiResponseRaw.trim().startsWith('"cards"')) {
            apiResponseRaw = '{' + apiResponseRaw + '}';
        }

        const apiResponse = JSON.parse(apiResponseRaw);

        // Extract items from apiResponse (it has "cards" array)
        let apiCards = [];
        if (apiResponse.data && Array.isArray(apiResponse.data.cards)) {
            apiCards = apiResponse.data.cards;
        } else if (apiResponse.cards && Array.isArray(apiResponse.cards)) {
            apiCards = apiResponse.cards;
        } else {
            // Fallback if structure is flat array
            apiCards = Array.isArray(apiResponse) ? apiResponse : [];
        }

        // Flatten episodes for easier searching
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

        console.log(`Loaded ${Object.keys(videoThumbnails).length} thumbnail entries and ${allEpisodes.length} API episodes.`);

        let matchCount = 0;
        let processedCount = 0;

        // Iterate over VideoThumbnails
        for (const key in videoThumbnails) {
            const vt = videoThumbnails[key];

            // FILTER: Only process files in DD_App_EncryptedVideos
            const adaptiveUrl = vt.AdaptiveStreamingVideoURL;
            if (!adaptiveUrl || !adaptiveUrl.includes('/DD_App_EncryptedVideos/')) {
                continue;
            }

            // Extract the base folder from the Adaptive URL
            // URL format: .../DD_App_EncryptedVideos/<FOLDER_NAME>/master.m3u8
            const parts = adaptiveUrl.split('/DD_App_EncryptedVideos/');
            if (parts.length < 2) continue;

            const folderPath = parts[1].split('/master.m3u8')[0];
            // e.g., ShreeMahakaleshwarJyotirlingaAarti4k_Encrypted

            // MATCHING: Find the corresponding episode in API response
            // Strategy: Match by Title
            const targetTitle = cleanString(vt.videoTitle);

            let matchedEpisode = allEpisodes.find(ep => {
                const epTitle = cleanString(ep.thumbnail?.title?.en);
                // Also check hindi title if strict match fails?
                // For now, simple strict title match
                return epTitle === targetTitle;
            });

            // Fallback: fuzzy match or try matching keys?
            if (!matchedEpisode) {
                console.warn(`Could not match video: "${vt.videoTitle}"`);
                continue;
            }

            matchCount++;

            // CONSTRUCT PAYLOAD
            const baseWebUrl = `https://s3.ap-south-1.amazonaws.com/co.techxr.system.backend.upload.dev/adaptiveStreaming/DD_App_EncryptedVideos/${folderPath}`;
            const awsKey = vt.AdaptiveStreamVideoKeyAWSObjectId;

            const newStreamingOptions = [
                {
                    "contentUrl": `${baseWebUrl}/master.m3u8`,
                    "streamingQuality": "ADAPTIVE",
                    "awsKey": awsKey,
                    "sizeInKb": null
                },
                {
                    "contentUrl": `${baseWebUrl}/output_4k/playlist.m3u8`,
                    "streamingQuality": "P_4320",
                    "awsKey": awsKey,
                    "sizeInKb": null
                },
                {
                    "contentUrl": `${baseWebUrl}/output_2.5k/playlist.m3u8`,
                    "streamingQuality": "P_2160",
                    "awsKey": awsKey,
                    "sizeInKb": null
                },
                {
                    "contentUrl": `${baseWebUrl}/output_2k/playlist.m3u8`,
                    "streamingQuality": "P_1440",
                    "awsKey": awsKey,
                    "sizeInKb": null
                },
                {
                    "contentUrl": `${baseWebUrl}/output_1080p/playlist.m3u8`,
                    "streamingQuality": "P_1080",
                    "awsKey": awsKey,
                    "sizeInKb": null
                }
            ];

            // EXECUTE UPDATE
            console.log(`Processing: ${vt.videoTitle} (ID: ${matchedEpisode.id})`);
            try {
                if (processedCount >= LIMIT_UPDATES) {
                    console.log(`Reached limit of ${LIMIT_UPDATES} updates. Stopping.`);
                    break;
                }

                await updateStreamingOptions(matchedEpisode.id, newStreamingOptions);
                processedCount++;
            } catch (error) {
                console.error(`Failed to update ${vt.videoTitle}:`, error);
            }
        }

        console.log(`\n--- SUMMARY ---`);
        console.log(`Total Relevant Videos: ${matchCount}`);
        console.log(`Successfully Processed: ${processedCount}`);

    } catch (err) {
        console.error("Critical Error:", err);
    }
}

main();

const fs = require('fs');
const https = require('https');
const path = require('path');

// --- CONFIGURATION ---
const ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzAzNzUwOTAsInVzZXJfbmFtZSI6IjEiLCJhdXRob3JpdGllcyI6WyJST0xFX0REQVBQX1VTRVIiLCJST0xFX0REX1BVSkFfQ0FTSElFUiIsIlJPTEVfRERfUFVKQV9NQU5BR0VSIiwiUk9MRV9ESVZJTkVfRlJBTkNISVNFRV9DQVNISUVSIiwiUk9MRV9ERF9QVUpBX0FETUlOIiwiUk9MRV9EREFQUF9BRE1JTiIsIlJPTEVfRElWSU5FX0FETUlOIiwiUk9MRV9ESVZJTkVfRlJBTkNISVNFRV9PUEVSQVRPUiIsIlJPTEVfRERBUFBfU1VQUE9SVCIsIlJPTEVfRElWSU5FX0ZSQU5DSElTRUVfQUNDT1VOVEFOVCIsIlJPTEVfRElWSU5FX0ZSQU5DSElTRUVfTUFOQUdFUiIsIlJPTEVfRElWSU5FX0ZSQU5DSElTRUUiLCJST0xFX0REQVBQX0NPTlRFTlRfTUFOQUdFUiIsIlJPTEVfRERfUFVKQV9NT0RFUkFUT1IiXSwianRpIjoibWRlT3F3WkY3Vzc3SVpSdUpfcEFrclVRRzhNIiwiY2xpZW50X2lkIjoidGVjaHhyIiwic2NvcGUiOlsiYWxsIl19.R4pbI_g0IEoFi6Fne2A8d9b4386Ec4OmqvbP5vCgd_stnmcRfzBDoiBSVEAMH42w2zSueDOY4Fda5X9i8abzMVFdG5gR6wqkk5oYzsSVsM7NI8kyHGPHgADTzg3CE1P7eRR8xDEN65BN_t_yzj9YozR2MTWlxKuM998gTnVu3jQ697GiJhuLk6WI3YGFvOkWwR-iIoRaIvqrhKU0A5t86fyEY7Plnn0GqhZOCFWUwHGmKUjWAvO06S0xlpYYMA2vrFCn5zuwksOJsBiJN2WO1uIKPPy55L_smqroa-VJLx1DSsj98rABq-cpUIUqYu7J-p3t-Lv4EANFrpCgg8r2Gg";
const HOST = "devgateway.techxrdev.in";
const AUDIO_FILE = path.join(__dirname, 'audio.json');
const RESPONSE_FILE = path.join(__dirname, 'response.json');

// Set LIMIT to a number (e.g., 5) to test on a few episodes.
// Set LIMIT to null to run for all episodes.
const LIMIT = null;

// Set DRY_RUN to true to log without making real requests.
const DRY_RUN = false;
// ---------------------

function createEpisodeRequest(cardId, payload) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify(payload);
        const options = {
            hostname: HOST,
            path: `/api/content/cms/cards/${cardId}/episodes`,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${ACCESS_TOKEN}`,
                'Content-Length': Buffer.byteLength(data)
            }
        };

        if (DRY_RUN) {
            console.log(`[DRY RUN] Would POST to ${HOST}${options.path}`);
            console.log(`[DRY RUN] Payload: ${data}`);
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
        // Load response.json to get cardId and track already uploaded episodes
        const responseData = JSON.parse(fs.readFileSync(RESPONSE_FILE, 'utf8'));
        const cardId = responseData.id;
        const uploadedEpisodes = responseData.episodes || [];
        const uploadedTitles = new Set(uploadedEpisodes.map(ep => ep.thumbnail.title.en));

        console.log(`Card ID: ${cardId}`);
        console.log(`Found ${uploadedEpisodes.length} already uploaded episodes.`);

        // Load audio.json for episode data
        const audioData = JSON.parse(fs.readFileSync(AUDIO_FILE, 'utf8'));
        const albumData = audioData.albumData;

        // Apply limit if specified
        const episodesToProcess = LIMIT ? albumData.slice(0, LIMIT) : albumData;

        console.log(`Total episodes in audio.json: ${albumData.length}`);
        console.log(`Processing up to ${episodesToProcess.length} episodes...`);

        for (let i = 0; i < episodesToProcess.length; i++) {
            const track = episodesToProcess[i];

            // Skip already uploaded episodes (matching by English title)
            if (uploadedTitles.has(track.TrackTitle_Eng)) {
                console.log(`[${i + 1}/${episodesToProcess.length}] Skipping "${track.TrackTitle_Eng}": Already uploaded.`);
                continue;
            }

            console.log(`[${i + 1}/${episodesToProcess.length}] Uploading "${track.TrackTitle_Eng}"...`);

            const payload = {
                thumbnail: {
                    title: {
                        hi: track.Track_Title_Hin,
                        en: track.TrackTitle_Eng
                    },
                    description: {
                        hi: track.Track_Title_Hin,
                        en: track.TrackTitle_Eng
                    },
                    imageUrl: track.thumbnailUrl_Portrait,
                    displayOrientation: "SQUARE"
                },
                streamingOptions: [
                    {
                        contentUrl: track.videoUrl,
                        streamingQuality: "ADAPTIVE",
                        awsKey: "",
                        sizeInKb: null
                    }
                ],
                episodeNumber: (i + 1).toString(),
                locked: true,
                status: "PUBLISHED",
                contentType: "AUDIO",
                sequenceNo: i
            };

            try {
                const result = await createEpisodeRequest(cardId, payload);
                console.log(`   Successfully uploaded. Status: ${result.status}`);
            } catch (error) {
                console.error(`   Failed to upload "${track.TrackTitle_Eng}". Status: ${error.status || 'Error'}`);
                console.error(`   Error Body: ${error.body || error.message}`);
                // Optional: Stop on first error to prevent inconsistent state
                process.exit(1);
            }

            // Small delay to prevent rate limiting
            if (!DRY_RUN) {
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
        }

        console.log("\nUpload process completed.");
    } catch (error) {
        console.error(`Critical Error: ${error.message}`);
    }
}

main();

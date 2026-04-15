const fs = require('fs');
const https = require('https');
const path = require('path');

// --- CONFIGURATION ---
const ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzY1MDQ0NTYsInVzZXJfbmFtZSI6IjEiLCJhdXRob3JpdGllcyI6WyJST0xFX0RJVklORV9ERVZJQ0VfU1VQUE9SVCIsIlJPTEVfRERBUFBfVVNFUiIsIlJPTEVfRERfUFVKQV9DQVNISUVSIiwiUk9MRV9ERF9QVUpBX01BTkFHRVIiLCJST0xFX0RJVklORV9URU1QTEVfVklFV19NQU5BR0VSIiwiUk9MRV9ESVZJTkVfRlJBTkNISVNFRV9DQVNISUVSIiwiUk9MRV9ERF9QVUpBX0FETUlOIiwiUk9MRV9ERF9LSVRfQkFDS09GRklDRSIsIlJPTEVfRERBUFBfQURNSU4iLCJST0xFX0RJVklORV9GUkFOQ0hJU0VFX09QRVJBVE9SIiwiUk9MRV9ESVZJTkVfQURNSU4iLCJST0xFX0RJVklORV9GUkFOQ0hJU0VFX0FDQ09VTlRBTlQiLCJST0xFX0REQVBQX1NVUFBPUlQiLCJST0xFX0RJVklORV9GUkFOQ0hJU0VFX01BTkFHRVIiLCJST0xFX0RJVklORV9GUkFOQ0hJU0VFIiwiUk9MRV9EREFQUF9DT05URU5UX01BTkFHRVIiLCJST0xFX0REX1BVSkFfTU9ERVJBVE9SIl0sImp0aSI6IlQtV3A5Ul9PWVR6eGVCREZvU2RPX1pQWnJzWSIsImNsaWVudF9pZCI6InRlY2h4ciIsInNjb3BlIjpbImFsbCJdfQ.qdDHJrZLvjhqDgTw9CtoKJAHZ8c_FFtNcq5f5_EcpQKPi3J79hRUfdKdFh1u10p-i05J7-ml7gEF382Tl5uFnE6OGhiN9SgML1XCFFJ01Z-Q91w_KWCHAG8hHo2Jeo6jH3cb_I9TH1A5nycWEoL8ZsscNGw7rNliWxE6cp9mNdH2IlPR6pY0w8BSsQQDsOuq7k3pkDH1iDadWjjoG69pF7su-GtWIyhfUlz7638JCrth-YQcfhFc7epaOxxywSVfm13tiyJ5x3fyBCf5q9rmnE9siVwIkRbSJo9r06TIZZNTGrM6pZ0IU4Hag-hxTBqvRpywQONhIB8SPMc1Lo-0ww";
const HOST = "k8uatgateway.techxrdev.in";
const INPUT_FILE = path.join(__dirname, 'updated-track-dtos-no-tags.json');

// Set DRY_RUN=true to preview requests without updating.
const DRY_RUN = false;

// Set LIMIT to a number (e.g. 5) to update only a few tracks.
// Set LIMIT=null to process all tracks.
const LIMIT = null;

// Optional pagination control when running in chunks.
const START_INDEX = 0;
// If true, script will explicitly send tags: [] to clear tags.
const FORCE_EMPTY_TAGS = false;

const REQUEST_DELAY_MS = 1000;
// ---------------------

function updateTrackRequest(trackId, payload) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify(payload);
        const options = {
            hostname: HOST,
            path: `/api/content/shubhdarshan/v1/admin/tracks/${trackId}`,
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${ACCESS_TOKEN}`,
                'Content-Length': Buffer.byteLength(data)
            }
        };

        if (DRY_RUN) {
            resolve({
                status: 200,
                body: 'Dry run success',
                endpoint: `https://${HOST}${options.path}`,
                payload
            });
            return;
        }

        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => {
                body += chunk;
            });
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
        const allTracks = JSON.parse(fs.readFileSync(INPUT_FILE, 'utf8'));
        if (!Array.isArray(allTracks)) {
            throw new Error('Input file must contain a JSON array of track DTOs.');
        }

        const sliced = allTracks.slice(START_INDEX);
        const tracksToProcess = LIMIT === null ? sliced : sliced.slice(0, LIMIT);

        console.log(`Input DTOs: ${allTracks.length}`);
        console.log(`START_INDEX: ${START_INDEX}`);
        console.log(`LIMIT: ${LIMIT === null ? 'ALL' : LIMIT}`);
        console.log(`Tracks to process: ${tracksToProcess.length}`);
        console.log(`DRY_RUN: ${DRY_RUN}`);

        let successCount = 0;
        let failCount = 0;
        let skippedCount = 0;

        for (let i = 0; i < tracksToProcess.length; i++) {
            const dto = tracksToProcess[i];
            const trackId = dto?.id;
            const title = dto?.thumbnail?.title?.en || 'N/A';
            const hasTags = Object.prototype.hasOwnProperty.call(dto, 'tags');
            const payload = FORCE_EMPTY_TAGS ? { ...dto, tags: [] } : dto;
            const endpoint = `https://${HOST}/api/content/shubhdarshan/v1/admin/tracks/${trackId}`;

            console.log(`\n[${i + 1}/${tracksToProcess.length}] ${title}`);
            console.log(`Track ID: ${trackId}`);
            console.log(`Endpoint: PUT ${endpoint}`);
            console.log(`Payload has tags key: ${hasTags}`);
            console.log(`FORCE_EMPTY_TAGS: ${FORCE_EMPTY_TAGS}`);

            if (!trackId) {
                skippedCount++;
                console.warn('Skipped: Missing id in DTO.');
                continue;
            }

            try {
                if (DRY_RUN) {
                    console.log('[DRY RUN] Payload to be sent:');
                    console.log(JSON.stringify(payload, null, 2));
                }

                const result = await updateTrackRequest(trackId, payload);
                console.log(`Success. Status: ${result.status}`);
                if (!DRY_RUN && result.body) {
                    console.log(`Response: ${result.body}`);
                    try {
                        const parsed = JSON.parse(result.body);
                        const returnedTags = Array.isArray(parsed?.tags) ? parsed.tags : parsed?.tags;
                        console.log(`Returned tags after update: ${JSON.stringify(returnedTags)}`);
                    } catch (e) {
                        // Ignore parse errors and keep raw response logging.
                    }
                }
                successCount++;
            } catch (error) {
                failCount++;
                console.error(`Failed. Status: ${error.status || 'Error'}`);
                console.error(`Error Body: ${error.body || error.message}`);
            }

            if (!DRY_RUN) {
                await new Promise((resolve) => setTimeout(resolve, REQUEST_DELAY_MS));
            }
        }

        console.log('\n--- SUMMARY ---');
        console.log(`Total selected: ${tracksToProcess.length}`);
        console.log(`Succeeded: ${successCount}`);
        console.log(`Failed: ${failCount}`);
        console.log(`Skipped: ${skippedCount}`);
    } catch (error) {
        console.error(`Critical Error: ${error.message}`);
        process.exit(1);
    }
}

main();

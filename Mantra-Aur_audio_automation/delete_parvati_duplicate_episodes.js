const fs = require('fs');
const https = require('https');
const path = require('path');

// --- CONFIGURATION ---
const ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzY1MDQ0NTYsInVzZXJfbmFtZSI6IjEiLCJhdXRob3JpdGllcyI6WyJST0xFX0RJVklORV9ERVZJQ0VfU1VQUE9SVCIsIlJPTEVfRERBUFBfVVNFUiIsIlJPTEVfRERfUFVKQV9DQVNISUVSIiwiUk9MRV9ERF9QVUpBX01BTkFHRVIiLCJST0xFX0RJVklORV9URU1QTEVfVklFV19NQU5BR0VSIiwiUk9MRV9ESVZJTkVfRlJBTkNISVNFRV9DQVNISUVSIiwiUk9MRV9ERF9QVUpBX0FETUlOIiwiUk9MRV9ERF9LSVRfQkFDS09GRklDRSIsIlJPTEVfRERBUFBfQURNSU4iLCJST0xFX0RJVklORV9GUkFOQ0hJU0VFX09QRVJBVE9SIiwiUk9MRV9ESVZJTkVfQURNSU4iLCJST0xFX0RJVklORV9GUkFOQ0hJU0VFX0FDQ09VTlRBTlQiLCJST0xFX0REQVBQX1NVUFBPUlQiLCJST0xFX0RJVklORV9GUkFOQ0hJU0VFX01BTkFHRVIiLCJST0xFX0RJVklORV9GUkFOQ0hJU0VFIiwiUk9MRV9EREFQUF9DT05URU5UX01BTkFHRVIiLCJST0xFX0REX1BVSkFfTU9ERVJBVE9SIl0sImp0aSI6IlQtV3A5Ul9PWVR6eGVCREZvU2RPX1pQWnJzWSIsImNsaWVudF9pZCI6InRlY2h4ciIsInNjb3BlIjpbImFsbCJdfQ.qdDHJrZLvjhqDgTw9CtoKJAHZ8c_FFtNcq5f5_EcpQKPi3J79hRUfdKdFh1u10p-i05J7-ml7gEF382Tl5uFnE6OGhiN9SgML1XCFFJ01Z-Q91w_KWCHAG8hHo2Jeo6jH3cb_I9TH1A5nycWEoL8ZsscNGw7rNliWxE6cp9mNdH2IlPR6pY0w8BSsQQDsOuq7k3pkDH1iDadWjjoG69pF7su-GtWIyhfUlz7638JCrth-YQcfhFc7epaOxxywSVfm13tiyJ5x3fyBCf5q9rmnE9siVwIkRbSJo9r06TIZZNTGrM6pZ0IU4Hag-hxTBqvRpywQONhIB8SPMc1Lo-0ww";
const HOST = "k8uatgateway.techxrdev.in";
const RESPONSE_FILE = path.join(__dirname, 'response.json');
const DRY_RUN = false; // Keep true first. Set false to perform actual delete.
const REQUEST_DELAY_MS = 1000;
// ---------------------

const TARGET_IDS = [
    // "69d3b8ba8fee055e7027c748",
    // "69d3b8ba8fee055e7027c725",
    // "69d3b8ba8fee055e7027c726",
    // "69d3b8ba8fee055e7027c727",
    // "69d3b8ba8fee055e7027c728",
    // "69d3b8ba8fee055e7027c729",
    // "69d3b8ba8fee055e7027c72b",
    // "69d3b8ba8fee055e7027c72c",
    // "69d3b8ba8fee055e7027c72d",
    // "69d3b8ba8fee055e7027c72e",
    // "69d3b8ba8fee055e7027c72f",
    // "69d3b8ba8fee055e7027c730",
    // "69d3b8ba8fee055e7027c731",
    // "69d3b8ba8fee055e7027c732",
    // "69d3b8ba8fee055e7027c733",
    // "69d3b8ba8fee055e7027c735",
    // "69d3b8ba8fee055e7027c736",
    // "69d3b8ba8fee055e7027c737",
    // "69d3b8ba8fee055e7027c738",
    // "69d3b8ba8fee055e7027c739",
    // "69d3b8ba8fee055e7027c73a",
    // "69d3b8ba8fee055e7027c73b",
    // "69d3b8ba8fee055e7027c73c",
    // "69d3b8ba8fee055e7027c73d",
    // "69d3b8ba8fee055e7027c73f",
    // "69d3b8ba8fee055e7027c740",
    // "69d3b8ba8fee055e7027c741",
    // "69d3b8ba8fee055e7027c742",
    // "69d3b8ba8fee055e7027c743",
    // "69d3b8ba8fee055e7027c744",
    // "69d3b8ba8fee055e7027c745",
    // "69d3b8ba8fee055e7027c746",
    // "69d3b8ba8fee055e7027c747",
    // "69d3b8ba8fee055e7027c774",
    // "69d3b8ba8fee055e7027c775",
    // "69d3b8ba8fee055e7027c776",
    // "69d3b8ba8fee055e7027c777",
    // "69d3b8ba8fee055e7027c778",
    // "69d3b8ba8fee055e7027c779",
    // "69d3b8ba8fee055e7027c77a",
    // "69d3b8ba8fee055e7027c77b",
    // "69d3b8ba8fee055e7027c77c",
    // "69d3b8ba8fee055e7027c77d",
    // "69d3b8ba8fee055e7027c77e",
    // "69d3b8ba8fee055e7027c77f"
];

function loadEpisodeIndex() {
    const responseData = JSON.parse(fs.readFileSync(RESPONSE_FILE, 'utf8'));
    const episodes = Array.isArray(responseData.content) ? responseData.content : [];
    const index = new Map();
    for (const ep of episodes) {
        if (ep && ep.id) {
            index.set(ep.id, ep);
        }
    }
    return index;
}

function deleteEpisodeRequest(episodeId) {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: HOST,
            path: `/api/content/shubhdarshan/v1/admin/tracks/${episodeId}`,
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${ACCESS_TOKEN}`
            }
        };

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
        req.end();
    });
}

async function main() {
    try {
        const episodeIndex = loadEpisodeIndex();

        console.log(`Total target IDs: ${TARGET_IDS.length}`);
        console.log(`DRY_RUN: ${DRY_RUN}`);

        let successCount = 0;
        let failCount = 0;
        let missingInResponseCount = 0;

        for (let i = 0; i < TARGET_IDS.length; i++) {
            const episodeId = TARGET_IDS[i];
            const episode = episodeIndex.get(episodeId);
            const title = episode?.thumbnail?.title?.en || 'N/A';
            const tags = Array.isArray(episode?.tags) ? episode.tags : [];
            const endpoint = `https://${HOST}/api/content/shubhdarshan/v1/admin/tracks/${episodeId}`;

            console.log(`\n[${i + 1}/${TARGET_IDS.length}] Episode ID: ${episodeId}`);
            console.log(`Title: ${title}`);
            console.log(`Tags: ${JSON.stringify(tags)}`);
            console.log(`Endpoint: DELETE ${endpoint}`);

            if (!episode) {
                missingInResponseCount++;
                console.warn('Warning: ID not found in local response.json content.');
            } else if (DRY_RUN) {
                // In dry run, print full episode payload so deletion scope is explicit.
                console.log('DTO snapshot to be deleted:');
                console.log(JSON.stringify(episode, null, 2));
            }

            if (DRY_RUN) {
                console.log('[DRY RUN] Skipped actual delete request.');
                successCount++;
                continue;
            }

            try {
                const result = await deleteEpisodeRequest(episodeId);
                console.log(`Deleted successfully. Status: ${result.status}`);
                if (result.body) {
                    console.log(`Response: ${result.body}`);
                }
                successCount++;
            } catch (error) {
                failCount++;
                console.error(`Delete failed. Status: ${error.status || 'Error'}`);
                console.error(`Error Body: ${error.body || error.message}`);
            }

            await new Promise((resolve) => setTimeout(resolve, REQUEST_DELAY_MS));
        }

        console.log('\n--- SUMMARY ---');
        console.log(`Total IDs: ${TARGET_IDS.length}`);
        console.log(`Processed successfully: ${successCount}`);
        console.log(`Failed: ${failCount}`);
        console.log(`Missing in response.json: ${missingInResponseCount}`);
    } catch (error) {
        console.error(`Critical Error: ${error.message}`);
        process.exit(1);
    }
}

main();

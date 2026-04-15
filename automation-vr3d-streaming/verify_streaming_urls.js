
const fs = require('fs');
const path = require('path');

const VIDEO_THUMBNAILS_PATH = path.join(__dirname, 'VideoThumbnails.json');
const API_RESPONSE_PATH = path.join(__dirname, 'vr-3d-response.json');

function cleanString(str) {
    if (!str) return '';
    return str.replace(/^\uFEFF/, '').trim();
}

async function main() {
    try {
        console.log("Loading data files...");
        let thumbnailsRaw = fs.readFileSync(VIDEO_THUMBNAILS_PATH, 'utf8');
        let apiResponseRaw = fs.readFileSync(API_RESPONSE_PATH, 'utf8');

        thumbnailsRaw = thumbnailsRaw.replace(/^\uFEFF/, '');
        apiResponseRaw = apiResponseRaw.replace(/^\uFEFF/, '');

        const videoThumbnails = JSON.parse(thumbnailsRaw);

        let apiResponse;
        try {
            apiResponse = JSON.parse(apiResponseRaw);
        } catch (e) {
            // Handle if it's wrapped or bare array
            if (apiResponseRaw.trim().startsWith('[')) {
                apiResponse = JSON.parse(apiResponseRaw);
            } else {
                console.error("Failed to parse API Response JSON");
                return;
            }
        }

        let apiCards = [];
        if (apiResponse.data && Array.isArray(apiResponse.data.cards)) {
            apiCards = apiResponse.data.cards;
        } else if (apiResponse.cards && Array.isArray(apiResponse.cards)) {
            apiCards = apiResponse.cards;
        } else if (Array.isArray(apiResponse)) {
            apiCards = apiResponse;
        } else {
            console.log("Could not find array of cards/episodes in API response structure:", Object.keys(apiResponse));
            return;
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
            } else if (card.streamingOptions) {
                // It might be a direct episode list if the user pasted just episodes?
                // But structure usually has cards. 
                // Let's assume the standard structure for now based on previous files.
                allEpisodes.push(card);
            }
        });

        console.log(`Loaded ${allEpisodes.length} episodes from API Response.`);

        // 1. Check for missing 2.5k videos
        console.log("\n--- Checking for 2.5k Quality URLs ---");
        let count2_5k = 0;
        const missing2_5k = [];

        allEpisodes.forEach(ep => {
            const has2_5k = ep.streamingOptions?.some(opt => {
                return (opt.contentUrl && opt.contentUrl.includes("2.5k")) ||
                    (opt.contentUrl && opt.contentUrl.includes("2500"));
            });

            if (has2_5k) {
                count2_5k++;
            } else {
                // Filter out DRAFT or ones that shouldn't have it?
                // The user says "suppose to be 59", so let's list all that DON'T have it.
                // We exclude those unrelated entirely if needed, but better to list and let user decide.

                // Only count "Published" or valid ones? 
                // User didn't specify, but let's check basic title
                const title = ep.thumbnail?.title?.en || "Unknown Title";
                missing2_5k.push({ id: ep.id, title: title });
            }
        });

        console.log(`Found ${count2_5k} episodes with 2.5k URL.`);
        console.log(`Expected 59. Missing candidates:`);
        missing2_5k.forEach(item => {
            console.log(` - [${item.id}] ${item.title}`);
        });


        // 2. Compare with VideoThumbnails.json
        console.log("\n--- Comparing with VideoThumbnails.json ---");

        let vtCount = 0;
        let matchedCount = 0;

        for (const key in videoThumbnails) {
            const vt = videoThumbnails[key];
            vtCount++;
            const vtTitle = cleanString(vt.videoTitle);

            // Find matching episode
            const match = allEpisodes.find(ep => {
                const epTitle = cleanString(ep.thumbnail?.title?.en);
                return epTitle === vtTitle;
            });

            if (match) {
                matchedCount++;
                // Check if Streaming URL matches AdaptiveStreamingVideoURL?
                // User asked "find does the respective fields are correctly match"

                // Let's check if the Adaptive URL in VT is present in the API response options?
                const vtUrl = vt.AdaptiveStreamingVideoURL;
                if (vtUrl) {
                    // Check if this URL exists in the episode's streaming options
                    // Usually it maps to the 'ADAPTIVE' quality or simply inclusion
                    const exists = match.streamingOptions?.some(opt => opt.contentUrl === vtUrl);

                    if (!exists) {
                        // It might be mismatch
                        console.log(`[MISMATCH URL] Title: "${vtTitle}"`);
                        console.log(`   VT URL:  ${vtUrl}`);
                        console.log(`   API has: ${match.streamingOptions?.length} options (None match exact string)`);
                    }
                } else {
                    // VT has no URL
                    // console.log(`[INFO] "${vtTitle}" has no Adaptive URL in VideoThumbnails.`);
                }

            } else {
                console.log(`[MISSING IN API] "${vtTitle}" present in Thumbnails but not found in API Response.`);
            }
        }

    } catch (err) {
        console.error("Error:", err);
    }
}

main();

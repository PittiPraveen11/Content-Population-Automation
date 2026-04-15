const fs = require('fs');

const videoThumbnails = JSON.parse(fs.readFileSync('VideoThumbnails.json', 'utf8').replace(/^\uFEFF/, ''));
let apiResponseRaw = fs.readFileSync('vr-3d-response.json', 'utf8').replace(/^\uFEFF/, '').trim();
if (apiResponseRaw.startsWith('"cards"')) {
    apiResponseRaw = '{' + apiResponseRaw + '}';
}
const apiResponse = JSON.parse(apiResponseRaw);

const PATTERN = "https://s3.ap-south-1.amazonaws.com/co.techxr.system.backend.upload.dev/adaptiveStreaming/DD_App_EncryptedVideos/";

// Get all titles/folders from VideoThumbnails matching PATTERN
const vtEntries = [];
for (const key in videoThumbnails) {
    const url = videoThumbnails[key].AdaptiveStreamingVideoURL;
    if (url && url.startsWith(PATTERN)) {
        vtEntries.push({
            title: videoThumbnails[key].videoTitle,
            url: url
        });
    }
}

console.log(`Total matching in VT: ${vtEntries.length}`);

// Get all matching in API Response
const apiEntries = [];
const apiCards = apiResponse.cards || apiResponse.data?.cards || [];
apiCards.forEach(card => {
    card.episodes.forEach(ep => {
        const adaptiveOpt = ep.streamingOptions.find(opt => opt.streamingQuality === 'ADAPTIVE');
        if (adaptiveOpt && adaptiveOpt.contentUrl && adaptiveOpt.contentUrl.startsWith(PATTERN)) {
            apiEntries.push({
                id: ep.id,
                title: ep.thumbnail?.title?.en,
                url: adaptiveOpt.contentUrl
            });
        }
    });
});

console.log(`Total matching in API: ${apiEntries.length}`);

// Find missing
const missing = vtEntries.filter(vt => {
    return !apiEntries.some(api => {
        // Match by title or by URL
        return (api.title && api.title.trim().toLowerCase() === vt.title.trim().toLowerCase()) ||
            (api.url === vt.url);
    });
});

console.log('\nMissing in API Response:');
missing.forEach(m => console.log(`- Title: "${m.title}", URL: ${m.url}`));

const fs = require('fs');

const response = JSON.parse(fs.readFileSync('vr-3d-response.json', 'utf8'));

let adaptiveCount = 0;
let p2160Count = 0;
const missingP2160 = [];

response.data.forEach(series => {
    if (series.episodes) {
        series.episodes.forEach(episode => {
            const streamingOptions = episode.streamingOptions || [];

            const hasAdaptive = streamingOptions.some(opt => opt.streamingQuality === 'ADAPTIVE');
            const hasP2160 = streamingOptions.some(opt => opt.streamingQuality === 'P_2160');

            if (hasAdaptive) {
                adaptiveCount++;
                if (!hasP2160) {
                    missingP2160.push({
                        id: episode.id,
                        title: episode.thumbnail?.title?.en || 'Unknown Title'
                    });
                }
            }
            if (hasP2160) {
                p2160Count++;
            }
        });
    }
});

console.log(`Total episodes with ADAPTIVE: ${adaptiveCount}`);
console.log(`Total episodes with P_2160: ${p2160Count}`);
console.log('Episodes with ADAPTIVE but missing P_2160:');
console.log(JSON.stringify(missingP2160, null, 2));

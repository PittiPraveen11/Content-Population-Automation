const fs = require('fs');
const path = require('path');

const VIDEO_THUMBNAILS_PATH = path.join(__dirname, 'VideoThumbnails.json');

function main() {
    try {
        let content = fs.readFileSync(VIDEO_THUMBNAILS_PATH, 'utf8');
        // Handle potential BOM
        content = content.replace(/^\uFEFF/, '');

        const data = JSON.parse(content);

        const path1 = "https://s3.ap-south-1.amazonaws.com/co.techxr.system.backend.upload.dev/adaptiveStreaming/DD_App_EncryptedVideos";
        const path2 = "https://s3.ap-south-1.amazonaws.com/co.techxr.system.backend.upload.dev/DurlabhDarshan6K/Encrypted/Hindi_100B";

        console.log("Videos NOT matching the expected adaptive paths:\n");
        console.log("ID\tTitle");
        console.log("--------------------------------------------------");

        let count = 0;
        for (const key in data) {
            const video = data[key];
            const url = video.AdaptiveStreamingVideoURL;

            if (!url || (!url.includes(path1) && !url.includes(path2))) {
                console.log(`${key}\t${video.videoTitle}`);
                count++;
            }
        }
        console.log(`\nTotal unmatched: ${count}`);

    } catch (err) {
        console.error("Error:", err);
    }
}

main();

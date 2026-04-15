const fs = require('fs');

try {
    const data = fs.readFileSync('/Users/pittipraveen/Downloads/techxr/xr-frontspace/automation-vr3d-streaming/vr-3d-response.json', 'utf8');
    const json = JSON.parse(data);

    // The structure might be an array or object. Let's inspect.
    let items = [];
    if (Array.isArray(json)) {
        items = json;
    } else if (json.data && Array.isArray(json.data)) {
        items = json.data;
    } else {
        console.log("Root is not an array. Keys:", Object.keys(json));
        // If it's an object with numbered keys like VideoThumbnails
        if (json["1"]) items = Object.values(json);
    }

    // Search for ID
    const targetId = "693942fa64add5b2e7343fef";
    let found = null;

    // Recursive search or simple flatten? 
    // CTA cards usually have episodes.

    function search(items) {
        for (const item of items) {
            if (item.id === targetId || item._id === targetId) return item;
            if (item.episodes) {
                for (const ep of item.episodes) {
                    if (ep.id === targetId || ep._id === targetId) return ep; // The ID might be an episode ID
                }
            }
        }
        return null;
    }

    found = search(items);

    if (found) {
        console.log("Found Object:", JSON.stringify(found, null, 2));
    } else {
        console.log("Object with ID " + targetId + " not found.");
        // Try searching by title
        items.forEach(item => {
            if (JSON.stringify(item).includes("Mahakaleshwar")) {
                console.log("Potential match (partial):", item.id || item.title || item.name);
            }
        });
    }

} catch (e) {
    console.error(e);
}

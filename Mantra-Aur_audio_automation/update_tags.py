import json
import re

with open('new-tracks-payload-deduped.json', 'r', encoding='utf-8') as f:
    payload = json.load(f)

with open('tsv-youtube-id-tag-map-corrected.json', 'r', encoding='utf-8') as f:
    tag_map = json.load(f)

def extract_youtube_id(url):
    if not url: return None
    match = re.search(r'(?:youtu\.be\/|youtube\.com\/(?:[^\/]+\/.+\/|(?:v|embed)\/|.*[?&]v=)|shorts\/)([^"&?\/\s]{11})', url, re.I)
    return match.group(1) if match else None

tag_map_lookup = {item['youtube_video_id']: item.get('tags', []) for item in tag_map if 'youtube_video_id' in item}

groups = {}
for i, item in enumerate(payload):
    if item.get('streamingOptions') and len(item['streamingOptions']) > 0:
        url = item['streamingOptions'][0].get('contentUrl')
        yt_id = extract_youtube_id(url)
        title_hi = item.get('thumbnail', {}).get('title', {}).get('hi')
        
        if yt_id and title_hi:
            key = f"{yt_id}|{title_hi}"
            if key not in groups:
                groups[key] = []
            groups[key].append(i)

indices_to_remove = set()
duplicate_count = 0

for key, indices in groups.items():
    if len(indices) > 1:
        duplicate_count += 1
        first_index = indices[0]
        yt_id = key.split('|')[0]
        
        # Tags from the map for this youtube ID
        mapped_tags = tag_map_lookup.get(yt_id, [])
        
        # Combine existing tags of all duplicates? The user said "union tags".
        # So we should gather tags from all duplicates of this video and the tag map.
        all_tags = set(mapped_tags)
        for idx in indices:
            all_tags.update(payload[idx].get('tags', []))
            
        # Update the first item
        payload[first_index]['tags'] = sorted(list(all_tags))
        
        # Mark remaining duplicates for removal
        for idx in indices[1:]:
            indices_to_remove.add(idx)

# Create new payload excluding marked indices
new_payload = [item for i, item in enumerate(payload) if i not in indices_to_remove]

with open('new-tracks-payload-deduped-updated.json', 'w', encoding='utf-8') as f:
    json.dump(new_payload, f, ensure_ascii=False, indent=2)

print(f"Found {duplicate_count} unique items that had duplicates.")
print(f"Total duplicates removed: {len(indices_to_remove)}")
print(f"Original length: {len(payload)}")
print(f"New length: {len(new_payload)}")

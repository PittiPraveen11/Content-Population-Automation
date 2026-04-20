import json
import re

print("Starting deduplication process...")

# 1. Read TSV Map
with open('tsv-youtube-id-tag-map-corrected.json', 'r', encoding='utf-8') as f:
    tag_map = json.load(f)

# 2. Filter map for items with exactly one title
filtered_tag_map = [item for item in tag_map if len(item.get('titles', [])) == 1]

# Save intermediate filtered list
with open('filtered-single-title-map.json', 'w', encoding='utf-8') as f:
    json.dump(filtered_tag_map, f, ensure_ascii=False, indent=2)

print(f"Generated filtered-single-title-map.json with {len(filtered_tag_map)} items.")

# 3. Create a lookup dict for fast matching: keys are youtube_id
single_title_lookup = {}
for item in filtered_tag_map:
    yt_id = item['youtube_video_id']
    title = item['titles'][0]
    tags = item.get('tags', [])
    single_title_lookup[yt_id] = {
        'title': title,
        'tags': set(tags)
    }

# 4. Read Payload
with open('new-tracks-payload-deduped.json', 'r', encoding='utf-8') as f:
    payload = json.load(f)

def extract_youtube_id(url):
    if not url: return None
    match = re.search(r'(?:youtu\.be\/|youtube\.com\/(?:[^\/]+\/.+\/|(?:v|embed)\/|.*[?&]v=)|shorts\/)([^"&?\/\s]{11})', url, re.I)
    return match.group(1) if match else None

# 5. Group payload indices matching the specified criteria
groups = {}
for i, item in enumerate(payload):
    if item.get('streamingOptions') and len(item['streamingOptions']) > 0:
        url = item['streamingOptions'][0].get('contentUrl')
        yt_id = extract_youtube_id(url)
        title_hi = item.get('thumbnail', {}).get('title', {}).get('hi')
        
        # Condition: Payload yt_id must be in our single_title_lookup AND payload title_hi must perfectly match the mapped single title
        if yt_id in single_title_lookup and title_hi == single_title_lookup[yt_id]['title']:
            key = f"{yt_id}|{title_hi}"
            if key not in groups:
                groups[key] = []
            groups[key].append(i)

indices_to_remove = set()
group_match_count = 0

# 6. Apply Union and Deduplication logic
for key, indices in groups.items():
    if len(indices) >= 1: # We apply logic even if it's 1 occurrence (0 duplicates), merging TSV tags!
        group_match_count += 1
        first_index = indices[0]
        yt_id = key.split('|')[0]
        
        # Use exactly the mapped tags from TSV
        all_tags = list(single_title_lookup[yt_id]['tags'])
        
        # Update the FIRST instance in payload
        payload[first_index]['tags'] = sorted(all_tags)
        
        # If there are duplicates, mark them for removal (Deduplication)
        if len(indices) > 1:
            for idx in indices[1:]:
                indices_to_remove.add(idx)

print(f"Matched {group_match_count} unique (youtube_id + title) groups from the TSV map criteria.")
print(f"Found and marked {len(indices_to_remove)} duplicate elements for removal.")

# 7. Generate updated payload
new_payload = [item for i, item in enumerate(payload) if i not in indices_to_remove]

with open('new-tracks-payload-deduped-updated.json', 'w', encoding='utf-8') as f:
    json.dump(new_payload, f, ensure_ascii=False, indent=2)

print(f"Original payload size: {len(payload)}")
print(f"Updated payload size: {len(new_payload)}")
print("Process completed successfully.")

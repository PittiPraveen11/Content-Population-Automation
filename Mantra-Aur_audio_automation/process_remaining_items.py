import json
import re

tsv_path = '/Users/pittipraveen/Downloads/company/techxr/Content-Population-Automation/Mantra-Aur_audio_automation/bhagwan ji ke mantra shlokas chalisa  - Sheet1.tsv'
json_path = '/Users/pittipraveen/Downloads/company/techxr/Content-Population-Automation/Mantra-Aur_audio_automation/new-tracks-payload-deduped.json'

with open(tsv_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# category mappings based on the text headings vs sections.json
cat_map = {
    "Peace of Mind": "Peace",
    "STRENGTH / PROTECTION": "Strength",
    "KNOWLEDGE / LEARNING": "Knowledge",
    "WEALTH / PROSPERITY": "Wealth",
    "LOVE / RELATIONSHIPS": "LoveAndRelationship",
    "HAPPINESS / DEVOTION": "Happiness",
    "HEALTH / HEALING": "Health",
    "SUCCESS / VICTORY / CAREER": "Success"
}

genre_map = {
    "Mantras": "Mantra",
    "Stotram / Ashtakam": "Strotam",
    "Stuti": "Stuti",
    "Shlokas": "Shloka",
    "Stotram / Ashtakam / kavach": "Strotam",
    "Chalisa": "Chalisa",
    "Aarti": "Aarti",
    "Stotram": "Strotam",
    "Bhajans": "Bhajan",
    "Katha": "Katha"
}

items = []
current_category = None
current_genre = None

for i in range(725, len(lines)):
    line = lines[i].strip('\n')
    line_s = line.strip()
    if not line_s:
        continue
        
    found_cat = False
    for k in cat_map.keys():
        if k in line_s:
            current_category = cat_map[k]
            found_cat = True
            break
    if found_cat: continue
    
    found_genre = False
    for k in genre_map.keys():
        if "🕉" in line_s or "📜" in line_s or "🙏" in line_s or "📖" in line_s or "Aarti" in line_s or "🎶" in line_s:
            if k in line_s:
                current_genre = genre_map[k]
                found_genre = True
                break
    if found_genre: continue
    
    cols = line.split('\t')
    urls = [c for c in cols if c.strip().startswith('http')]
    if not urls: continue
    
    url = urls[-1].strip()
    
    non_empty = [c.strip() for c in cols if c.strip() and not c.strip().startswith('http')]
    if 'क्रम संख्या' in line or 'मंत्र का नाम' in line or 'यूट्यूब लिंक' in line or 'क्रम' in non_empty[0] or 'प्रकार (Type)' in line:
        continue
        
    if not non_empty: continue
    
    title = non_empty[0]
    if len(non_empty) > 1 and re.match(r'^\d+$', title):
        title = non_empty[1]
        
    items.append({
        "title_hi": title,
        "url": url,
        "category": current_category,
        "genre": current_genre
    })

print(f"Total extracted items: {len(items)}")

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

def get_yt_id(url):
    m = re.search(r'(?:v=|youtu\.be/|shorts/)([^&?]+)', url)
    return m.group(1) if m else url

existing_map = {}
for idx, item in enumerate(data):
    opts = item.get('streamingOptions', [])
    if not opts: continue
    url = opts[0].get('contentUrl', '')
    yt_id = get_yt_id(url)
    title_hi = item.get('thumbnail', {}).get('title', {}).get('hi', '')
    
    key = f"{yt_id}:::{title_hi}"
    existing_map[key] = idx

items_to_insert = []
updated_count = 0

for new_item in items:
    yt_id = get_yt_id(new_item['url'])
    key = f"{yt_id}:::{new_item['title_hi']}"
    
    tags_to_add = [new_item['category'], new_item['genre']]
    tags_to_add = [t for t in tags_to_add if t]
    
    if key in existing_map:
        idx = existing_map[key]
        added = False
        for tag in tags_to_add:
            if tag not in data[idx]['tags']:
                data[idx]['tags'].append(tag)
                added = True
        if added:
            updated_count += 1
    else:
        dto = {
            "thumbnail": {
                "title": {
                    "hi": new_item['title_hi'],
                    "en": new_item['title_hi']  # using hindi spelling as fallback
                },
                "imageUrl": None,
                "iconUrl": None,
                "description": {
                    "hi": new_item['title_hi'],
                    "en": new_item['title_hi']
                },
                "displayOrientation": "SQUARE"
            },
            "streamingOptions": [
                {
                    "contentUrl": new_item['url'],
                    "streamingQuality": "ADAPTIVE",
                    "awsKey": None,
                    "sizeInKb": 0
                }
            ],
            "status": "DRAFT",
            "tags": tags_to_add,
            "locked": False
        }
        items_to_insert.append(dto)

print(f"Updated existing items: {updated_count}")
print(f"New items to insert: {len(items_to_insert)}")

for item in items_to_insert:
    data.append(item)

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Saved successfully.")

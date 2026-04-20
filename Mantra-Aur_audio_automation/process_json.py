import json
import re

tsv_path = '/Users/pittipraveen/Downloads/company/techxr/Content-Population-Automation/Mantra-Aur_audio_automation/bhagwan ji ke mantra shlokas chalisa  - Sheet1.tsv'
json_path = '/Users/pittipraveen/Downloads/company/techxr/Content-Population-Automation/Mantra-Aur_audio_automation/new-tracks-payload-deduped.json'

with open(tsv_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

tag_mapping = {
    "सुबह उठते ही": "SubahUthteHi",
    "नहाने के समय": "NahaneKeSamay",
    "नहाने के बाद": "NahaneKeBaad",
    "भोजन से पहले": "BhojanSePehle",
    "भोजन के बाद": "BhojanKeBaad",
    "पूजा के समय": "PoojaKeSamay",
    "पूजा के बाद": "PoojaKeBaad",
    "सोने से पहले": "SoneSePehle"
}

transliterations = {
    "करादर्शनम्": "Karadarshanam",
    "पृथ्वी क्षमा प्रार्थना": "Prithvi Kshama Prarthana",
    "नवग्रह प्रभात मंत्र": "Navgrah Prabhat Mantra",
    "मंगल स्मरण मंत्र": "Mangal Smaran Mantra",
    "पंचकन्या स्मरण": "Panchkanya Smaran",
    "स्नान मंत्र": "Snan Mantra",
    "वरुण मंत्र": "Varun Mantra",
    "सूर्य अर्घ्य": "Surya Arghya",
    "गायत्री मंत्र": "Gayatri Mantra",
    "शिव पंचाक्षर": "Shiv Panchakshar",
    "चंदन लगाने का मंत्र": "Chandan Lagane Ka Mantra",
    "तुलसी प्रार्थना": "Tulsi Prarthana",
    "ब्रह्मार्पण मंत्र": "Brahmarpan Mantra",
    "अन्नपूर्णा स्तुति": "Annapurna Stuti",
    "शांति मंत्र": "Shanti Mantra",
    "अगस्त्य मंत्र": "Agastya Mantra",
    "कृतज्ञता": "Kritagyata",
    "चरणामृत मंत्र": "Charanamrit Mantra",
    "आसन मंत्र": "Aasan Mantra",
    "दीप मंत्र": "Deep Mantra",
    "गणेश वंदना": "Ganesh Vandana",
    "गुरु वंदना": "Guru Vandana",
    "अर्पण मंत्र": "Arpan Mantra",
    "आचमन मंत्र": "Aachaman Mantra",
    "पुष्पाञ्जलि श्लोक": "Pushpanjali Shloka",
    "पूर्णमदः मंत्र": "Purnamadah Mantra",
    "प्रदक्षिणा मंत्र": "Pradakshina Mantra",
    "हनुमान मंत्र": "Hanuman Mantra",
    "रक्षा मंत्र": "Raksha Mantra",
    "शयन मंत्र": "Shayan Mantra",
    "क्षमा याचना": "Kshama Yachana",
    "विष्णु स्मरण": "Vishnu Smaran"
}

new_items = []
current_tag = None

for i in range(673, 722):
    line = lines[i].strip('\n')
    cols = line.split('\t')
    
    non_empty = [c for c in cols if c.strip()]
    if len(non_empty) == 1 and non_empty[0] in tag_mapping:
        current_tag = tag_mapping[non_empty[0]]
        continue
        
    if len(cols) >= 6:
        url = None
        for col in reversed(cols):
            if col.startswith('http'):
                url = col
                break
        
        if not url:
            continue
            
        title = cols[1].strip() if cols[1].strip() and cols[1].strip() != '-' else cols[2].strip()[:30]
        if title == "अगस्त्य मंत्र":
            current_tag = "BhojanKeBaad"
            
        new_items.append({
            "title_hi": title,
            "title_en": transliterations.get(title, title),
            "url": url,
            "tag": current_tag
        })

# Load JSON
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

def get_yt_id(url):
    m = re.search(r'(?:v=|youtu\.be/|shorts/)([^&?]+)', url)
    return m.group(1) if m else url

# Build dict of existing items based on ID + title
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
for new_item in new_items:
    yt_id = get_yt_id(new_item['url'])
    key = f"{yt_id}:::{new_item['title_hi']}"
    
    if key in existing_map:
        # Update existing
        idx = existing_map[key]
        if new_item['tag'] and new_item['tag'] not in data[idx]['tags']:
            data[idx]['tags'].append(new_item['tag'])
        # if the user also requested 'Mantra' or something, 'actual tags just the other diety ones'
        if "Mantra" not in data[idx]['tags']:
            pass # wait, let's not assume they want 'Mantra' on everything, user said 'actual tags and dtos just the other diety ones' (just like)
    else:
        # Create new DTO
        dto = {
            "thumbnail": {
                "title": {
                    "hi": new_item['title_hi'],
                    "en": new_item['title_en']
                },
                "imageUrl": None,
                "iconUrl": None,
                "description": {
                    "hi": new_item['title_hi'],
                    "en": new_item['title_en']
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
            "tags": [new_item['tag']],
            "locked": False
        }
        items_to_insert.append(dto)

print(f"Items to insert: {len(items_to_insert)}")

# Find index to insert
insert_idx = -1
for idx, item in enumerate(data):
    if item.get('thumbnail', {}).get('title', {}).get('hi') == "माता पार्वती का कठिन तप और शिव से विवाह":
        insert_idx = idx + 1
        # wait there might be multiple? The user said after DurgaMataJi ones, line 11140. 
        # let's just find the first one that appears.
        
if insert_idx == -1:
    print("Could not find insertion point!")
else:
    print(f"Inserting {len(items_to_insert)} items at index {insert_idx}...")
    for item in reversed(items_to_insert):
        data.insert(insert_idx, item)
    
    # Save back
    with open('/Users/pittipraveen/Downloads/company/techxr/Content-Population-Automation/Mantra-Aur_audio_automation/new-tracks-payload-deduped.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Saved successfully.")


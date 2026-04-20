import json

tsv_path = '/Users/pittipraveen/Downloads/company/techxr/Content-Population-Automation/Mantra-Aur_audio_automation/bhagwan ji ke mantra shlokas chalisa  - Sheet1.tsv'

with open(tsv_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_items = []
current_tag = None
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

for i in range(673, 722):
    line = lines[i].strip('\n')
    cols = line.split('\t')
    
    # check for section header
    non_empty = [c for c in cols if c.strip()]
    if len(non_empty) == 1 and non_empty[0] in tag_mapping:
        current_tag = tag_mapping[non_empty[0]]
        continue
        
    if len(cols) >= 6:
        # sometimes url is at cols[6] if there are double tabs
        url = None
        for col in reversed(cols):
            if col.startswith('http'):
                url = col
                break
        
        if not url:
            continue
            
        title = cols[1].strip() if cols[1].strip() and cols[1].strip() != '-' else cols[2].strip()[:30]
        if title == "अगस्त्य मंत्र":
            current_tag = "BhojanKeBaad" # handled edge case found previously
            
        new_items.append({
            "title_hi": title,
            "url": url,
            "tag": current_tag
        })

print(f"Total items extracted: {len(new_items)}")
for it in new_items:
    print(f'"{it["title_hi"]}": "",')


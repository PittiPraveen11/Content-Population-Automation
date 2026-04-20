import re
import json

tsv_path = '/Users/pittipraveen/Downloads/company/techxr/Content-Population-Automation/Mantra-Aur_audio_automation/bhagwan ji ke mantra shlokas chalisa  - Sheet1.tsv'

with open(tsv_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

def get_yt_id(url):
    m = re.search(r'(?:v=|youtu\.be/|shorts/)([^&?\s]+)', url)
    return m.group(1) if m else url

# State variables
current_deity = None
current_genre = None
current_daily = None
current_intent = None
current_festival = None

# Mappings
deity_map = {
    "SHIV JI": "Shivji", "HANUMAN JI": "HanumanJi", "GANESH JI": "GaneshJi",
    "VISHNU JI": "VishnuJi", "LAKSHMI JI": "LakshmiJi", "SHANII DEV JI": "ShaniiDevJi",
    "RAM JI": "Ramji", "KRISHNA JI": "KrishnaJi", "DURJA JI": "DurjaJi"
}
genre_map = {
    "MANTRA": "Mantra", "STOTRAM": "Strotam", "CHALISA": "Chalisa",
    "ASHTAKAM": "Ashtakam", "STUTI": "Stuti", "AARTI": "Aarti",
    "SHLOKAS": "Shloka", "BHAJAN": "Bhajan", "KATHA": "Katha"
}
daily_map = {
    "सुबह उठते ही": "SubahUthteHi", "नहाने के समय": "NahaneKeSamay",
    "नहाने के बाद": "NahaneKeBaad", "भोजन से पहले": "BhojanSePehle",
    "भोजन के बाद": "BhojanKeBaad", "पूजा के समय": "PoojaKeSamay",
    "पूजा के बाद": "PoojaKeBaad", "सोने से पहले": "SoneSePehle"
}
intent_map = {
    "Peace of Mind": "Peace", "STRENGTH / PROTECTION": "Strength",
    "KNOWLEDGE / LEARNING": "Knowledge", "WEALTH / PROSPERITY": "Wealth",
    "LOVE / RELATIONSHIPS": "LoveAndRelationship", "HAPPINESS / DEVOTION": "Happiness",
    "HEALTH / HEALING": "Health", "SUCCESS / VICTORY / CAREER": "Success"
}
festival_map = {
    "DIWALI": "Diwali", "Janmashtami": "Janmashtami", "Dussehra": "Dussehra",
    "Maha Shivratri": "MahaShivratri", "Ganesh Chaturthi": "GaneshChaturthi",
    "Ram Navami": "RamNavami", "Hanuman Jayanti": "HanumanJayanti"
}

url_tags = {}

def process_line(line_text, line_idx):
    global current_deity, current_genre, current_daily, current_intent, current_festival
    
    line_s = line_text.strip()
    
    # Identify Section Transitions
    if line_idx < 674:
        # Deity section
        current_daily = current_intent = current_festival = None
        for k, v in deity_map.items():
            if k in line_text:
                current_deity = v
    elif 674 <= line_idx < 724:
        # Daily section
        current_deity = current_genre = current_intent = current_festival = None
        for k, v in daily_map.items():
            if k in line_text:
                current_daily = v
    elif 724 <= line_idx < 1254:
        # Intent section
        current_deity = current_daily = current_festival = None
        for k, v in intent_map.items():
            if k in line_text:
                current_intent = v
    else:
        # Festival section
        current_deity = current_daily = current_intent = None
        for k, v in festival_map.items():
            if k in line_text:
                current_festival = v
                
    # Detect Genre (can be anywhere except Daily)
    # Be careful not to misclassify substrings, checking roughly
    upper_line = line_s.upper()
    if "MANTRA" in upper_line: current_genre = "Mantra"
    elif "STOTRAM" in upper_line: current_genre = "Strotam"
    elif "CHALISA" in upper_line: current_genre = "Chalisa"
    elif "ASHTAKAM" in upper_line: current_genre = "Ashtakam"
    elif "STUTI" in upper_line: current_genre = "Stuti"
    elif "AARTI" in upper_line: current_genre = "Aarti"
    elif "SHLOKA" in upper_line: current_genre = "Shloka"
    elif "BHAJAN" in upper_line: current_genre = "Bhajan"
    elif "KATHA" in upper_line: current_genre = "Katha"
    
    # Process Item
    cols = line_text.split('\t')
    urls = [c.strip() for c in cols if "http" in c]
    if not urls: return
    
    url = urls[-1]
    yt_id = get_yt_id(url)
    
    tags = set([t for t in [current_deity, current_genre, current_daily, current_intent, current_festival] if t])
    
    if yt_id not in url_tags:
        url_tags[yt_id] = set()
        
    url_tags[yt_id].update(tags)

for i, line in enumerate(lines):
    process_line(line, i)

# Serialize to JSON
output = {k: list(v) for k, v in url_tags.items()}
with open('corrected_tags_map.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
    
print(f"Generated tags for {len(output)} unique YouTube IDs.")

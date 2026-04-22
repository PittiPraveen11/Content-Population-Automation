import json
import os
import re
import csv
import binascii

# Paths
BASE_DIR = "/Users/pittipraveen/Downloads/company/techxr/Content-Population-Automation/Mantra-Aur_audio_automation/Bhajan"
GCP_LINKS_DIR = os.path.join(BASE_DIR, "gcpLinks")

TARGET_FILE = os.path.join(GCP_LINKS_DIR, "cleandataDTO copy.json")
DEFAULT_IMAGE = "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Default/Default.webp"

GENRES = ['mantra', 'aarti', 'chalisa', 'strotam', 'stuti', 'shloka', 'katha', 'bhajan', 'ashtakam']

INTENT_MAP = {
    "peace_of_mind": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/BhajanHomeThumbnails/Intent/Peace.jpg",
    "Strength": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/BhajanHomeThumbnails/Intent/Strength.jpg",
    "Success": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/BhajanHomeThumbnails/Intent/Success.jpg",
    "Knowledge": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/BhajanHomeThumbnails/Intent/Knowledge.jpg",
    "Wealth": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/BhajanHomeThumbnails/Intent/Wealth.jpg",
    "LoveAndRelationship": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/BhajanHomeThumbnails/Intent/LoveAndRelationship.jpg",
    "Happiness": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/BhajanHomeThumbnails/Intent/Happiness.jpg",
    "Health": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/BhajanHomeThumbnails/Intent/Health.jpg"
}

BLACKLIST_FUZZY = ["mantra", "strotam", "beej mantra", "chalisa", "aarti", "shloka", "katha", "stuti", "arogya mantra", "shanti mantra"]

def normalize_title(title):
    if not title:
        return ""
    title = title.lower().strip()
    title = re.sub(r'[^a-z0-9\s\u0900-\u097f]', '', title)
    return title

def get_genre(text):
    if not text: return None
    text = text.lower()
    for g in GENRES:
        if g in text:
            return g
    return None

def split_camel_case(s):
    return re.sub('([a-z])([A-Z])', r'\1 \2', s)

def extract_name_from_content_url(url):
    if not url: return ""
    parts = url.split('/')
    if len(parts) > 2:
        name = parts[-2]
        if name.lower() == "index.m3u8": return ""
        return split_camel_case(name)
    return ""

def extract_title_from_url(url):
    if not url: return ""
    filename = url.split('/')[-1]
    name = filename.split('.')[0]
    name = re.sub(r'_[0-9]x$', '', name)
    name = name.replace('_', ' ')
    return name

def get_hash_index(key, length):
    if length == 0: return 0
    return binascii.crc32(key.encode()) % length

def build_libraries():
    specific_match_lib = {} # (NormalizedTitle, Deity) -> URL
    deity_genre_pools = {}  # Deity -> Genre -> [URLs]
    
    source_files = []
    for d in [BASE_DIR, GCP_LINKS_DIR]:
        for f in os.listdir(d):
            if f.endswith(".json") and f not in ["cleandataDTO copy.json", "image_mapping_draft.json"]:
                source_files.append(os.path.join(d, f))

    for file_path in source_files:
        if not os.path.exists(file_path): continue
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            all_tracks = []
            def extract_tracks(obj):
                if isinstance(obj, list): [extract_tracks(i) for i in obj]
                elif isinstance(obj, dict):
                    if "thumbnail" in obj: all_tracks.append(obj)
                    else:
                        for v in obj.values(): extract_tracks(v)
            extract_tracks(data)

            for track in all_tracks:
                img_url = track.get("thumbnail", {}).get("imageUrl")
                if not img_url or "Default.webp" in img_url: continue
                
                parts = img_url.split('/')
                deity = "Unknown"
                if "BhajanThumbnails" in parts:
                    idx = parts.index("BhajanThumbnails")
                    if idx + 1 < len(parts): deity = parts[idx + 1]
                
                if deity not in deity_genre_pools: 
                    deity_genre_pools[deity] = {"all": set()}
                
                filename = parts[-1].lower()
                genre = get_genre(filename)
                
                titles = []
                t_obj = track.get("thumbnail", {}).get("title", {})
                if isinstance(t_obj, dict):
                    if t_obj.get("en"): titles.append(t_obj.get("en"))
                    if t_obj.get("hi"): titles.append(t_obj.get("hi"))
                url_title = extract_title_from_url(img_url)
                if url_title: titles.append(url_title)

                for t in titles:
                    norm = normalize_title(t)
                    if norm:
                        specific_match_lib[(norm, deity)] = img_url
                        # If the title had a genre, add to genre pool
                        t_genre = get_genre(norm)
                        if t_genre:
                            if t_genre not in deity_genre_pools[deity]:
                                deity_genre_pools[deity][t_genre] = set()
                            deity_genre_pools[deity][t_genre].add(img_url)
                
                # Also add based on filename genre
                if genre:
                    if genre not in deity_genre_pools[deity]:
                        deity_genre_pools[deity][genre] = set()
                    deity_genre_pools[deity][genre].add(img_url)
                deity_genre_pools[deity]["all"].add(img_url)

        except: pass
            
    # Convert sets to sorted lists for deterministic indexing
    for deity in deity_genre_pools:
        for genre in deity_genre_pools[deity]:
            deity_genre_pools[deity][genre] = sorted(list(deity_genre_pools[deity][genre]))

    return specific_match_lib, deity_genre_pools

def main():
    specific_lib, deity_pools = build_libraries()
    print(f"Library built. Deities: {list(deity_pools.keys())}")

    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        target_data = json.load(f)

    draft_data = json.loads(json.dumps(target_data)) # deep copy
    mappings_report = []
    
    total_missing = 0
    total_matched = 0

    deity_alias = {
        "shivji": "Shivji", "hanumanji": "HanumanJi", "ganeshji": "GaneshJi",
        "vishnuji": "VishnuJi", "lakshmiji": "MaaLakshmiJi", "shaniidevji": "ShaniDevJi",
        "durjaji": "DurgaMataJi", "ramji": "RamJi", "krishnaji": "KrishnaJi"
    }

    for deity_id, categories in draft_data.items():
        if not isinstance(categories, dict): continue
        
        lib_deity = deity_alias.get(deity_id.lower())
        
        for category_id, tracks in categories.items():
            if not isinstance(tracks, list): continue
            
            for track in tracks:
                if track.get("thumbnail", {}).get("imageUrl") is not None: continue
                
                total_missing += 1
                title_en = track.get("thumbnail", {}).get("title", {}).get("en", "")
                title_hi = track.get("thumbnail", {}).get("title", {}).get("hi", "")
                content_url = track.get("streamingOptions", [{}])[0].get("contentUrl", "")
                
                assigned_url = DEFAULT_IMAGE
                match_type = "Default"

                norm_en = normalize_title(title_en)
                norm_hi = normalize_title(title_hi)
                content_name = extract_name_from_content_url(content_url)
                norm_content = normalize_title(content_name)
                track_genre = get_genre(norm_en) or get_genre(norm_content) or get_genre(category_id)

                # STAGE 1 & 2: Direct / Nearly Close Matches
                found = False
                if lib_deity and lib_deity in deity_pools:
                    # Specific Title match
                    for n in [norm_en, norm_content, norm_hi]:
                        if n and (n, lib_deity) in specific_lib:
                            assigned_url, match_type, found = specific_lib[(n, lib_deity)], "Direct Match", True
                            break
                    
                    # Fuzzy match within deity
                    if not found:
                        target_words = set(norm_en.split()) | set(norm_content.split())
                        for (lib_title, l_deity), url in specific_lib.items():
                            if l_deity != lib_deity or lib_title in BLACKLIST_FUZZY: continue
                            lib_words = set(lib_title.split())
                            intersection = target_words.intersection(lib_words)
                            if len(intersection) >= 2 or (len(intersection) >= 1 and any(len(w) > 7 for w in intersection)):
                                assigned_url, match_type, found = url, f"Fuzzy ({lib_title})", True
                                break

                # STAGE 3: Genre-Matched Deity Pool
                if not found and lib_deity and lib_deity in deity_pools:
                    if track_genre and track_genre in deity_pools[lib_deity]:
                        pool = deity_pools[lib_deity][track_genre]
                        idx = get_hash_index(title_en, len(pool))
                        assigned_url, match_type, found = pool[idx], f"Random {lib_deity} {track_genre}", True
                    # If specific genre pool empty, try "all" for deity ONLY if user wants (they said genre-matched first)
                    # User said: "instead of random one pick nearly close one if not then intent icons then after that choose default one"
                    # Wait, they also said "i am okey but instad of applying the aarti image to mantra try to upload the mantra rleated images"
                    # This implies: Nearly Close -> Genre-Specific Deity -> Intent -> Default.

                # STAGE 4: Generic Intent Fallback
                if not found:
                    if deity_id in INTENT_MAP:
                        assigned_url, match_type, found = INTENT_MAP[deity_id], "Intent Icon", True
                    elif category_id in INTENT_MAP:
                        assigned_url, match_type, found = INTENT_MAP[category_id], "Intent Icon", True

                # FINAL: Global Default (Match type remains "Default")

                if found: total_matched += 1
                track["thumbnail"]["imageUrl"] = assigned_url
                mappings_report.append({
                    "Deity": deity_id, "Category": category_id,
                    "Title EN": title_en, "Assigned Image": assigned_url, "Match Logic": match_type
                })

    # Save Mapping Report
    csv_path = os.path.join(GCP_LINKS_DIR, "image_mapping_report.csv")
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["Deity", "Category", "Title EN", "Assigned Image", "Match Logic"])
        writer.writeheader()
        writer.writerows(mappings_report)

    # Save Draft JSON
    draft_path = os.path.join(GCP_LINKS_DIR, "image_mapping_draft.json")
    with open(draft_path, 'w', encoding='utf-8') as f:
        json.dump(draft_data, f, ensure_ascii=False, indent=2)

    print(f"Summary: {total_missing} missing, {total_matched} matched, {total_missing - total_matched} defaulted.")
    print(f"Report: {csv_path}")

if __name__ == "__main__":
    main()

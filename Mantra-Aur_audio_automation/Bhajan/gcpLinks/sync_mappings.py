import json
import os

CLEAN_DATA_PATH = '/Users/pittipraveen/Downloads/company/techxr/Content-Population-Automation/Mantra-Aur_audio_automation/Bhajan/gcpLinks/cleandataDTO copy.json'
MAPPING_JSON_PATH = '/Users/pittipraveen/Downloads/company/techxr/Content-Population-Automation/Mantra-Aur_audio_automation/Bhajan/gcpLinks/mapping.json'
BASE_URL = 'https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/'

def sync():
    # 1. Load Data
    with open(CLEAN_DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open(MAPPING_JSON_PATH, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
        
    # 2. Build Filename -> Folder Map from existing data
    filename_to_folder = {}
    for deity_key, categories in data.items():
        if not isinstance(categories, dict): continue
        for cat_key, tracks in categories.items():
             for track in tracks:
                img_url = track.get('thumbnail', {}).get('imageUrl')
                if img_url:
                    parts = img_url.split('/')
                    if len(parts) >= 2:
                        folder = parts[-2]
                        filename = parts[-1]
                        filename_to_folder[filename] = folder
    
    # 3. Handle Special Fixes in mapping memory
    # The user's mapping file had a slight typo for this one
    target_typo = 'om_namoh_bhagwate_vasudevay_4x.webp'
    correct_name = 'om_namoh_bhagwate_vasudevaye_4x.webp'
    
    for d in mapping:
        for c in mapping[d]:
            for title, fname in mapping[d][c].items():
                if fname == target_typo:
                    mapping[d][c][title] = correct_name
                    
    # Ensure our lookup knows the correct name is in KrishnaJi
    filename_to_folder[correct_name] = 'KrishnaJi'
    
    # 4. Perform Sync
    updated_count = 0
    already_present_count = 0
    skipped_no_map_count = 0
    
    for deity_key, categories in data.items():
        if not isinstance(categories, dict): continue
        
        # We need to find the deity in the mapping.
        # mapping.json keys are exact deity names as per user's paste.
        mapping_deity = mapping.get(deity_key)
        
        for cat_key, tracks in categories.items():
            for track in tracks:
                current_img = track.get('thumbnail', {}).get('imageUrl')
                
                # Check if missing
                if current_img is None or current_img == "":
                    # Try to find a mapping
                    match_found = False
                    if mapping_deity:
                        # Categories in mapping.json (Mantra, Strotam, etc.) 
                        # usually match cat_key, but SubahUthteHi etc. use 'General'
                        
                        # Try exact category match
                        map_cat_data = mapping_deity.get(cat_key)
                        # Fallback to 'General' if category not found (for daily routine buckets)
                        if not map_cat_data:
                            map_cat_data = mapping_deity.get('General')
                            
                        if map_cat_data:
                            title_en = track.get('thumbnail', {}).get('title', {}).get('en')
                            if title_en in map_cat_data:
                                fname = map_cat_data[title_en]
                                
                                # Reconstruct URL
                                if fname == 'Default.webp':
                                    folder = 'Default'
                                else:
                                    folder = filename_to_folder.get(fname)
                                
                                if folder:
                                    full_url = f"{BASE_URL}{folder}/{fname}"
                                    track['thumbnail']['imageUrl'] = full_url
                                    updated_count += 1
                                    match_found = True
                    
                    if not match_found:
                        skipped_no_map_count += 1
                else:
                    already_present_count += 1
                    
    # 5. Save results
    with open(CLEAN_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Sync complete.")
    print(f"Updated (previously missing): {updated_count}")
    print(f"Skipped (already present): {already_present_count}")
    print(f"Skipped (missing but no mapping found): {skipped_no_map_count}")

if __name__ == '__main__':
    sync()

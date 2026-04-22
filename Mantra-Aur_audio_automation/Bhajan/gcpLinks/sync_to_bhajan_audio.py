import json

SOURCE_PATH = '/Users/pittipraveen/Downloads/company/techxr/Content-Population-Automation/Mantra-Aur_audio_automation/Bhajan/gcpLinks/cleandataDTO copy.json'
TARGET_PATH = '/Users/pittipraveen/Downloads/company/techxr/Content-Population-Automation/Mantra-Aur_audio_automation/Bhajan/gcpLinks/BajanAudio.json'

def sync_to_bhajan_audio():
    # 1. Load Source Data and build map
    with open(SOURCE_PATH, 'r', encoding='utf-8') as f:
        source_data = json.load(f)
    
    # lookup[(deity_or_section, category_or_genre, title_en)] = imageUrl
    mapping_lookup = {}
    
    for deity, categories in source_data.items():
        if not isinstance(categories, dict): continue
        for cat, tracks in categories.items():
            for track in tracks:
                img = track.get('thumbnail', {}).get('imageUrl')
                title_en = track.get('thumbnail', {}).get('title', {}).get('en')
                if img and title_en:
                    # Use a normalized key
                    mapping_lookup[(deity.lower(), cat.lower(), title_en.lower().strip())] = img

    print(f"Built mapping lookup with {len(mapping_lookup)} entries.")

    # 2. Load Target Data
    with open(TARGET_PATH, 'r', encoding='utf-8') as f:
        target_data = json.load(f)
        
    # 3. Traverse and Update
    stats = {
        'total_tracks': 0,
        'updated': 0,
        'already_present': 0,
        'no_mapping': 0
    }

    # BajanAudio has: Root -> Section -> Deity -> Genre -> [Tracks]
    # some sections might be flatter, so we handle both.
    
    sections_to_check = ['DEITY', 'GENRE', 'Daily Routine', 'INTENT', 'FESTIVAL SPECIAL']
    
    for section_name in sections_to_check:
        if section_name not in target_data: continue
        section_content = target_data[section_name]
        
        # inside section, usually we have Deities/Sections
        for entity_name, genres in section_content.items():
            if not isinstance(genres, dict): continue
            
            for genre_name, tracks in genres.items():
                if not isinstance(tracks, list): continue
                
                for track in tracks:
                    stats['total_tracks'] += 1
                    current_img = track.get('thumbnail', {}).get('imageUrl')
                    
                    if not current_img: # handles None or empty string
                        title_en = track.get('thumbnail', {}).get('title', {}).get('en')
                        if title_en:
                            # Try to match
                            lookup_key = (entity_name.lower(), genre_name.lower(), title_en.lower().strip())
                            
                            # Fallback mapping for Daily Routine items if category names mismatch
                            # (some use General in mapping, but might have different genre in target)
                            if lookup_key not in mapping_lookup:
                                lookup_key = (entity_name.lower(), 'general', title_en.lower().strip())

                            if lookup_key in mapping_lookup:
                                track['thumbnail']['imageUrl'] = mapping_lookup[lookup_key]
                                stats['updated'] += 1
                            else:
                                stats['no_mapping'] += 1
                        else:
                            stats['no_mapping'] += 1
                    else:
                        stats['already_present'] += 1
                    
    # 4. Save Target Data
    with open(TARGET_PATH, 'w', encoding='utf-8') as f:
        json.dump(target_data, f, ensure_ascii=False, indent=2)
        
    print(f"Synchronization Complete.")
    print(f"Total Tracks Checked: {stats['total_tracks']}")
    print(f"Updated (Missing Image Filled): {stats['updated']}")
    print(f"Skipped (Already Present): {stats['already_present']}")
    print(f"Skipped (No Mapping Found): {stats['no_mapping']}")

if __name__ == '__main__':
    sync_to_bhajan_audio()

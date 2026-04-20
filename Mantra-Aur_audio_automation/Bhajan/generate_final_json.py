import json
import os

def generate_json():
    base_path = '/Users/pittipraveen/Downloads/company/techxr/Content-Population-Automation/Mantra-Aur_audio_automation/Bhajan'
    home_file = os.path.join(base_path, 'BhajanHome.json')
    audio_file = os.path.join(base_path, 'BhajanAudio.json')
    output_file = os.path.join(base_path, 'BhajanFinalData.json')

    with open(home_file, 'r') as f:
        home_data = json.load(f)
    
    with open(audio_file, 'r') as f:
        audio_tracks = json.load(f)

    # Map tags to their types
    tag_to_type = {}
    type_to_tags = {
        "DEITY": set(),
        "GENRE": set(),
        "INTENT": set(),
        "DAILY ROUTINE": set(),
        "FESTIVAL SPECIAL": set()
    }

    for item in home_data:
        t = item.get('type')
        tag = item.get('tag')
        if t and tag:
            tag_to_type[tag] = t
            if t in type_to_tags:
                type_to_tags[t].add(tag)

    # Initialize collections
    final_data = {
        "home": home_data,
        "deity_collections": {},
        "intent_collections": {},
        "festival_collections": {},
        "genre_collections": {},
        "routine_collections": {}
    }

    # Helper to add track to nested dict
    def add_to_nested(d, key1, key2, track):
        if key1 not in d:
            d[key1] = {}
        if key2 not in d[key1]:
            d[key1][key2] = []
        # Avoid duplicate tracks in the same group (if track object is same)
        # However, tracks might be modified per group? No, just the track object.
        d[key1][key2].append(track)

    for track in audio_tracks:
        tags = track.get('tags', [])
        
        # Identify track categories
        track_deities = [t for t in tags if t in type_to_tags["DEITY"]]
        track_genres = [t for t in tags if t in type_to_tags["GENRE"]]
        track_intents = [t for t in tags if t in type_to_tags["INTENT"]]
        track_routines = [t for t in tags if t in type_to_tags["DAILY ROUTINE"]]
        track_festivals = [t for t in tags if t in type_to_tags["FESTIVAL SPECIAL"]]

        # 1. Deity Collections (Grouped by Genre)
        for deity in track_deities:
            for genre in track_genres:
                add_to_nested(final_data["deity_collections"], deity, genre, track)
            if not track_genres:
                add_to_nested(final_data["deity_collections"], deity, "General", track)

        # 2. Intent Collections (Grouped by Genre)
        for intent in track_intents:
            for genre in track_genres:
                add_to_nested(final_data["intent_collections"], intent, genre, track)
            if not track_genres:
                add_to_nested(final_data["intent_collections"], intent, "General", track)

        # 3. Festival Collections (Grouped by Genre)
        for festival in track_festivals:
            for genre in track_genres:
                add_to_nested(final_data["festival_collections"], festival, genre, track)
            if not track_genres:
                add_to_nested(final_data["festival_collections"], festival, "General", track)

        # 4. Genre Collections (Grouped by Deity, Intent, Festival)
        for genre in track_genres:
            if genre not in final_data["genre_collections"]:
                final_data["genre_collections"][genre] = {
                    "ByDeity": {},
                    "ByIntent": {},
                    "ByFestival": {}
                }
            
            # Group by Deity
            for deity in track_deities:
                if deity not in final_data["genre_collections"][genre]["ByDeity"]:
                    final_data["genre_collections"][genre]["ByDeity"][deity] = []
                final_data["genre_collections"][genre]["ByDeity"][deity].append(track)
            
            # Group by Intent
            for intent in track_intents:
                if intent not in final_data["genre_collections"][genre]["ByIntent"]:
                    final_data["genre_collections"][genre]["ByIntent"][intent] = []
                final_data["genre_collections"][genre]["ByIntent"][intent].append(track)
            
            # Group by Festival
            for festival in track_festivals:
                if festival not in final_data["genre_collections"][genre]["ByFestival"]:
                    final_data["genre_collections"][genre]["ByFestival"][festival] = []
                final_data["genre_collections"][genre]["ByFestival"][festival].append(track)

            # If no deity/intent/festival, we could add a "General" group here too if needed.
            # But the requirement was "we need show them as well" which implies these are the sub-categories.

        # 5. Routine Collections (Flat List)
        for routine in track_routines:
            if routine not in final_data["routine_collections"]:
                final_data["routine_collections"][routine] = []
            final_data["routine_collections"][routine].append(track)

    # Save final JSON
    with open(output_file, 'w') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully generated {output_file}")

if __name__ == "__main__":
    generate_json()

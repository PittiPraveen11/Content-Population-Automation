import json
import os

def extract_tracks_with_external_tags():
    home_file = "Home.json"
    ids_file = "draftWIthids.json"
    output_file = "TracksWithExternalTags.json"
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    home_path = os.path.join(script_dir, home_file)
    ids_path = os.path.join(script_dir, ids_file)
    output_path = os.path.join(script_dir, output_file)
    
    # Check if files exist
    if not os.path.exists(home_path):
        print(f"Error: {home_file} not found.")
        return
    if not os.path.exists(ids_path):
        print(f"Error: {ids_file} not found.")
        return

    # 1. Load Home.json and build a set of internal tags
    print(f"Loading {home_file}...")
    with open(home_path, 'r', encoding='utf-8') as f:
        home_data = json.load(f)
    
    internal_tags = set()
    for item in home_data:
        if isinstance(item, dict) and 'tag' in item and item['tag']:
            internal_tags.add(item['tag'])
    
    print(f"Found {len(internal_tags)} unique internal tags in {home_file}.")

    # 2. Load draftWIthids.json
    print(f"Loading {ids_file}...")
    with open(ids_path, 'r', encoding='utf-8') as f:
        ids_data = json.load(f)
    
    all_tracks = ids_data.get('content', [])
    print(f"Analyzing {len(all_tracks)} tracks from {ids_file}...")

    # 3. Filter tracks
    external_tracks = []
    seen_external_tags = set()
    
    for track in all_tracks:
        track_tags = track.get('tags', [])
        # Find if any tag in the track is NOT in the internal_tags set
        external_tags_in_track = [t for t in track_tags if t not in internal_tags]
        
        if external_tags_in_track:
            external_tracks.append(track)
            seen_external_tags.update(external_tags_in_track)

    print(f"Filtering complete.")
    print(f"Number of tracks with external tags: {len(external_tracks)}")
    print(f"Sample of external tags found: {list(seen_external_tags)[:10]}...")

    # 4. Save the full DTOs to the new file
    print(f"Saving {len(external_tracks)} DTOs to {output_file}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(external_tracks, f, indent=4, ensure_ascii=False)
    
    print("Done!")

if __name__ == "__main__":
    extract_tracks_with_external_tags()

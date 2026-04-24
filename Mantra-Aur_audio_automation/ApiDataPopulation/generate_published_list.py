import json
import os
from collections import defaultdict

def get_key(track):
    """Generates a composite key for matching tracks."""
    url = ""
    if track.get('streamingOptions'):
        url = track['streamingOptions'][0].get('contentUrl', '')
    
    title = track.get('thumbnail', {}).get('title', {}).get('en', '')
    tags = tuple(sorted(track.get('tags', [])))
    
    return (url, title, tags)

def generate_filtered_list():
    draft_file = "draft.json"
    ids_file = "draftWIthids.json"
    output_file = "FilteredPublishedTracksWithIds.json"
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    draft_path = os.path.join(script_dir, draft_file)
    ids_path = os.path.join(script_dir, ids_file)
    output_path = os.path.join(script_dir, output_file)
    
    if not os.path.exists(draft_path) or not os.path.exists(ids_path):
        print(f"Error: Required files not found.")
        return

    print(f"Loading {ids_file} to build ID lookup table...")
    with open(ids_path, 'r', encoding='utf-8') as f:
        ids_data = json.load(f)
    
    id_lookup = defaultdict(list)
    tracks_with_ids = ids_data.get('content', [])
    for track in tracks_with_ids:
        key = get_key(track)
        id_lookup[key].append(track)

    print(f"Loading {draft_file} as the filter source...")
    with open(draft_path, 'r', encoding='utf-8') as f:
        source_tracks = json.load(f)

    print(f"Matching {len(source_tracks)} source tracks...")
    
    output_list = []
    match_count = 0
    fail_count = 0
    
    for source in source_tracks:
        key = get_key(source)
        if key in id_lookup and id_lookup[key]:
            # Take the first available match (queue approach)
            match = id_lookup[key].pop(0)
            
            # Use the data from the ID file but ensure status is PUBLISHED
            # (We preserve the ID and other metadata from the server response)
            match['status'] = "PUBLISHED"
            output_list.append(match)
            match_count += 1
        else:
            fail_count += 1
            title = source.get('thumbnail', {}).get('title', {}).get('en', 'Unknown')
            print(f"Warning: No matching ID found for track: {title}")

    print(f"\n--- Results ---")
    print(f"Total Source Tracks: {len(source_tracks)}")
    print(f"Successfully Matched: {match_count}")
    print(f"Failed to Match: {fail_count}")
    
    if match_count > 0:
        print(f"Saving filtered list to {output_file}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_list, f, indent=4, ensure_ascii=False)
        print("Done!")
    else:
        print("Error: No tracks were matched. Output file not created.")

if __name__ == "__main__":
    generate_filtered_list()

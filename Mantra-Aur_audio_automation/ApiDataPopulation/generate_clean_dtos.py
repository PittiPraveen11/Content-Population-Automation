import json
import os

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_valid_tags(home_data):
    # Use 'tag' or 'code' – usually they are the same. In Home.json, we'll use 'tag' if present, else 'code'.
    valid_tags = set()
    for item in home_data:
        t = item.get('tag') or item.get('code')
        if t:
            valid_tags.add(t)
    return valid_tags

def create_dto(track, tags):
    # Ensure tags are unique and sorted for consistency
    clean_tags = sorted(list(set(tags)))
    
    dto = {
        "thumbnail": {
            "title": track['thumbnail']['title'],
            "imageUrl": track['thumbnail']['imageUrl'],
            "iconUrl": None,
            "description": track['thumbnail'].get('description', track['thumbnail']['title']),
            "displayOrientation": "SQUARE"
        },
        "streamingOptions": [
            {
                "contentUrl": opt['contentUrl'],
                "streamingQuality": "ADAPTIVE",
                "awsKey": None,
                "sizeInKb": 0
            } for opt in track.get('streamingOptions', [])
        ],
        "status": "DRAFT",
        "tags": clean_tags,
        "locked": False
    }
    return dto

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    home_file = os.path.join(script_dir, "Home.json")
    input_file = os.path.join(script_dir, "AInputForApi.json")
    output_file = os.path.join(script_dir, "CleanTracksDTO.json")

    home_data = load_json(home_file)
    input_data = load_json(input_file)
    valid_tags = get_valid_tags(home_data)

    print(f"Loaded {len(valid_tags)} valid tags from Home.json")

    clean_dtos = []
    total_tracks_processed = 0

    # Categories in AInputForApi.json
    # DEITY, Daily Routine, INTENT, FESTIVAL SPECIAL
    
    # Process DEITY
    if 'DEITY' in input_data:
        for deity, genres in input_data['DEITY'].items():
            for genre, tracks in genres.items():
                # Filter tags
                track_tags = []
                if deity in valid_tags: track_tags.append(deity)
                if genre in valid_tags: track_tags.append(genre)
                
                for track in tracks:
                    clean_dtos.append(create_dto(track, track_tags))
                    total_tracks_processed += 1

    # Process INTENT
    if 'INTENT' in input_data:
        for intent, genres in input_data['INTENT'].items():
            for genre, tracks in genres.items():
                track_tags = []
                if intent in valid_tags: track_tags.append(intent)
                if genre in valid_tags: track_tags.append(genre)
                
                for track in tracks:
                    clean_dtos.append(create_dto(track, track_tags))
                    total_tracks_processed += 1

    # Process FESTIVAL SPECIAL
    if 'FESTIVAL SPECIAL' in input_data:
        for festival, genres in input_data['FESTIVAL SPECIAL'].items():
            for genre, tracks in genres.items():
                track_tags = []
                if festival in valid_tags: track_tags.append(festival)
                if genre in valid_tags: track_tags.append(genre)
                
                for track in tracks:
                    clean_dtos.append(create_dto(track, track_tags))
                    total_tracks_processed += 1

    # Process Daily Routine
    # "for daily routine we only have one tag in tags array"
    # Daily Routine -> RoutineName -> misc -> Tracks
    if 'Daily Routine' in input_data:
        for routine, subcats in input_data['Daily Routine'].items():
            for subcat, tracks in subcats.items():
                # subcat is usually 'misc', but we should skip it
                track_tags = []
                if routine in valid_tags: track_tags.append(routine)
                
                for track in tracks:
                    clean_dtos.append(create_dto(track, track_tags))
                    total_tracks_processed += 1

    save_json(clean_dtos, output_file)
    print(f"Processed {total_tracks_processed} tracks.")
    print(f"Generated clean DTOs in {output_file}")

    # Double check 'misc' removal
    for dto in clean_dtos:
        if 'misc' in dto['tags']:
            print("Warning: 'misc' found in tags!")
            break

if __name__ == "__main__":
    main()

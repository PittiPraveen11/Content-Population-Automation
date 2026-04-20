import json
import sys

file_path = 'new-tracks-payload-deduped.json'

def main():
    print(f"Loading {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return

    # Find duplicates
    seen = {}
    
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        
        # Extract properties safely
        streaming_opts = item.get('streamingOptions', [])
        content_url = None
        if streaming_opts and isinstance(streaming_opts, list) and len(streaming_opts) > 0:
            content_url = streaming_opts[0].get('contentUrl')
        
        thumbnail = item.get('thumbnail', {})
        title_obj = thumbnail.get('title', {}) if isinstance(thumbnail, dict) else {}
        title_en = title_obj.get('en') if isinstance(title_obj, dict) else None
        
        tags = item.get('tags', [])
        tags_tuple = tuple(sorted(tags)) if isinstance(tags, list) else tuple()

        if content_url and title_en:
            key = (content_url, title_en, tags_tuple)
            if key in seen:
                seen[key].append(idx)
            else:
                seen[key] = [idx]

    # Collect groups that have more than 1 item
    indices_to_remove = []
    quit_early = False

    for key, indices in seen.items():
        if len(indices) > 1:
            content_url, title_en, tags = key
            
            # Keep the first one, ask about the rest
            first_idx = indices[0]
            
            for dup_idx in indices[1:]:
                print("\n" + "="*60)
                print(f"DUPLICATE FOUND")
                print(f"Title EN : {title_en}")
                print(f"Tags     : {list(tags)}")
                print(f"URL      : {content_url}")
                print(f"Original Index : {first_idx} (Keeping this one)")
                print(f"Duplicate Index: {dup_idx} (Candidate for deletion)")
                print("="*60)
                
                while True:
                    choice = input("Do you want to DELETE the duplicate? (y/n/q to quit): ").strip().lower()
                    if choice in ['y', 'n', 'q']:
                        break
                    print("Invalid input. Please enter 'y', 'n', or 'q'.")
                    
                if choice == 'q':
                    print("Exiting interactive mode...")
                    quit_early = True
                    break
                elif choice == 'y':
                    indices_to_remove.append(dup_idx)
                    print(f"-> Marked index {dup_idx} for deletion.")
                else:
                    print(f"-> Skipped. Index {dup_idx} will be kept.")
            
            if quit_early:
                break

    # Remove items in reverse order so indices don't shift during deletion
    indices_to_remove.sort(reverse=True)

    if indices_to_remove:
        print("\n" + "="*60)
        print(f"Removing {len(indices_to_remove)} confirmed duplicates...")
        for idx in indices_to_remove:
            del data[idx]

        # Save the file
        print(f"Saving updated data directly to {file_path}...")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print("Successfully updated the JSON file!")
    else:
        print("\nNo items were marked for deletion. File remains unchanged.")

if __name__ == "__main__":
    main()

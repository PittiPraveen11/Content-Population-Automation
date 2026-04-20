import json
import os

base_dir = "/Users/pittipraveen/Downloads/company/techxr/Content-Population-Automation/Wallpapers/HinduSanathanWallpapers"
json_path = "/Users/pittipraveen/Downloads/company/techxr/Content-Population-Automation/Wallpapers/deities-wallpapers.json"

folder_to_id = {
    "DurgaJi": "durga_ji",
    "HanumanJi": "hanuman_ji",
    "KrishnaJi": "krishna_ji",
    "LaxmiJi": "laxmi_ji",
    "RadhaRani": "radha_rani",
    "RamJi": "ram_ji",
    "ShivJi": "shiv_ji",
    "VishnuJi": "vishnu_ji"
}

with open(json_path, 'r') as f:
    data = json.load(f)

count = 0

for deity in data['deities']:
    folder_name = None
    for k, v in folder_to_id.items():
        if v == deity['id']:
            folder_name = k
            break
    
    if not folder_name:
        continue
        
    folder_path = os.path.join(base_dir, folder_name)
    if not os.path.exists(folder_path):
        continue
        
    files = [f for f in os.listdir(folder_path) if f.endswith('.webp')]
    files.sort()
    
    for file in files:
        name_no_ext = os.path.splitext(file)[0]
        suffix = name_no_ext.replace("frame_", "")
        new_id = f"{deity['id']}_portrait_{suffix}"
        
        image_url = f"https://ddappcdn.techxr.co/HinduSanatanWallpapersAndStatus/Portraits/{folder_name}/{file}"
        
        new_wallpaper = {
            "id": new_id,
            "imageUrl": image_url,
            "isFree": False
        }
        
        deity['wallpapers'].append(new_wallpaper)
        count += 1

with open(json_path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    # Add a newline at the end of the file since json.dump does not do it
    f.write("\n")

print(f"Added {count} new wallpapers with isFree=False to deities-wallpapers.json")

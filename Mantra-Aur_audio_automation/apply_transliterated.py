import csv
import json

payload_path = 'new-tracks-payload.json'
csv_path = 'transliterated.csv'

with open(payload_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Read the CSV
updates = {}
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader) # skip header
    for row in reader:
        if len(row) >= 3:
            track_num = int(row[0])
            title = row[1].strip()
            desc = row[2].strip()
            updates[track_num] = (title, desc)

# Update payload
for i, item in enumerate(data):
    track_num = i + 1
    if track_num in updates:
        title, desc = updates[track_num]
        item['thumbnail']['title']['en'] = title
        item['thumbnail']['description']['en'] = desc

with open(payload_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Updated {len(updates)} records out of {len(data)} total records.")

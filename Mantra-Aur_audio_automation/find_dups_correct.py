import json

filename = 'new-tracks-payload-deduped.json'
output_filename = 'duplicates_list.md'

with open(filename, 'r') as f:
    data = json.load(f)

groups = {}
for i, item in enumerate(data):
    # contentUrl is in streamingOptions[0]['contentUrl']
    contentUrl = ''
    streaming_options = item.get('streamingOptions', [])
    if streaming_options and isinstance(streaming_options, list) and len(streaming_options) > 0:
        contentUrl = streaming_options[0].get('contentUrl', '')
        
    # title_en is in thumbnail['title']['en']
    title_en = ''
    thumbnail = item.get('thumbnail', {})
    if thumbnail and isinstance(thumbnail, dict):
        title = thumbnail.get('title', {})
        if title and isinstance(title, dict):
            title_en = title.get('en', '')
            
    tags = item.get('tags', [])
    tag_set = frozenset(tags) if isinstance(tags, list) else frozenset()
    
    key = (contentUrl, title_en, tag_set)
    if key not in groups:
        groups[key] = []
    groups[key].append(i)

dups = {k: v for k, v in groups.items() if len(v) > 1}

with open(output_filename, 'w') as out:
    out.write(f"# Duplicates List ({len(dups)} groups found)\n\n")
    out.write("Items with the same `contentUrl`, `thumbnail.title.en`, and `tags` (ignoring order).\n\n")
    for k, v in dups.items():
        url = k[0] or '(empty)'
        title = k[1] or '(empty)'
        tags = list(k[2])
        out.write(f"### Title EN: `{title}`\n")
        out.write(f"- **Content URL**: `{url}`\n")
        out.write(f"- **Tags**: {tags}\n")
        out.write(f"- **Indices in JSON**: {v} (Total: {len(v)})\n\n")

print(f"Generated {output_filename} with {len(dups)} duplicates.")

import csv

with open('/Users/pittipraveen/Downloads/company/techxr/Content-Population-Automation/Mantra-Aur_audio_automation/bhagwan ji ke mantra shlokas chalisa  - Sheet1.tsv', 'r') as f:
    lines = f.readlines()

print("Lines 673-676:")
for i in range(673, min(677, len(lines))):
    cols = lines[i].strip('\n').split('\t')
    print(f"{i+1}: {cols}")
    
# Let's see how many items we are actually talking about between 674 and 722
items = []
current_tag = None
for i in range(673, 722):
    cols = lines[i].strip('\n').split('\t')
    if len(cols) >= 6 and cols[5].startswith('http'):
        title = cols[1].strip() if cols[1].strip() and cols[1] != '-' else cols[2][:30]
        desc = cols[3]
        link = cols[5]
        items.append((title, desc, link, current_tag))
    else:
        # maybe it's a category
        text = [c for c in cols if c.strip()]
        if text and not text[0].startswith('http'):
            current_tag = text[0]
            print(f"Found tag: {current_tag}")

print(f"Found {len(items)} items")
for item in items[:2]:
    print(item)


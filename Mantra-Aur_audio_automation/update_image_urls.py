import json

def update_tracks():
    mapping = {
        "Panchakshari Mantra": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/pancha_shri_mantra_4x.webp",
        "Mahamrityunjay Mantra": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/mahamritunjay_4x.webp",
        "Rudra Mantra": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/rudra_mantra_4x.webp",
        "Shiv Gayatri Mantra": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/shiv_gyatri_mantra_4x.webp",
        "Shiv Stuti Mantra": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/shiv_stuti_mantra_4x.webp",
        "Shiv Tandav Stotram": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/shiv_tandav_4x.webp",
        "Shiv Panchakshar Stotram": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/shiv_panchakshar_4x.webp",
        "Shiv Mahimn Stotra": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/shiv_mahiman_4x.webp",
        "Vedasar Shiv Stotram": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/vedsaar_4x.webp",
        "Shiv Chalisa": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/shiv_chalisa_4x.webp",
        "Rudrashtakam": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/shiv_rudrashtakam_4x.webp",
        "Shiv Stuti": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/shiv_stuti_4x.webp",
        "Om Jai Shiv Omkara": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/shiv_aarti_4x.webp",
        "Dhyan Shlok": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/shiv_shlok_4x.webp",
        "Shiv Shankar Ko Jisne Puja": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/shiv_shankar_ko_jisne_pooja_4x.webp",
        "Subah Subah Le Shiv Ka Naam": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/subha_subha_le_shiv_ka_naam_4x.webp",
        "He Shambhu Baba": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/hey_shambhu_baba_4x.webp",
        "Chalo Shiv Shankar Ke Mandir": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/chale_shiv_shankar_ke_mandir_4x.webp",
        "Bhole Bhandari": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/bhole_bhandari_4x.webp",
        "Shankar Teri Jata Mein": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/gangaadhara_4x.webp",
        "Sampurn Shiv Puran Saar": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/shiv_puran_saar_4x.webp",
        "Shiv Ji Ka Janm": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/shiv_janma_katha_4x.webp",
        "Neelkanth Katha": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/neelkhanth_gatha_4x.webp",
        "Neelkanth": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/neelkhanth_gatha_4x.webp",
        "Nandi Story": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/nandi_kaise_bane_shiv_ki_sawari_4x.webp",
        "Nandi": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/nandi_kaise_bane_shiv_ki_sawari_4x.webp",
        "Ardhanarishvara Story": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/ardhanarishvara_4x.webp",
        "Ardhanarishwar": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/ardhanarishvara_4x.webp",
        "Chandrama Shrap": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/chandrama_shrap_4x.webp",
        "Chandrama": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/chandrama_shrap_4x.webp",
        "12 Jyotirling": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/12_jyotirlinga_4x.webp",
        "Ganesh Story": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/ganesh_ji_4x.webp",
        "Ganesh": "https://ddappcdn.techxr.co/ShubhDarshan/Thumbnails/BhajanThumbnails/Shivji/ganesh_ji_4x.webp",
    }
    
    # Sort keys by length in reverse to avoid matching substring early (e.g., "Shiv Stuti" before "Shiv Stuti Mantra")
    sorted_keys = sorted(mapping.keys(), key=len, reverse=True)

    with open('new-tracks-payload.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    updated_count = 0
    not_found = set(mapping.keys())

    for track in data:
        en_title = track.get('thumbnail', {}).get('title', {}).get('en', '').strip()
        if not en_title:
            continue
            
        for key in sorted_keys:
            if key in en_title:
                track['thumbnail']['imageUrl'] = mapping[key]
                updated_count += 1
                if key in not_found:
                    not_found.remove(key)
                break  # stop matching for this track since we assigned the longest matching key

    with open('new-tracks-payload.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Updated {updated_count} tracks.")
    if not_found:
        print("These keys were not matched at all:")
        for k in not_found:
            print("-", k)

if __name__ == '__main__':
    update_tracks()

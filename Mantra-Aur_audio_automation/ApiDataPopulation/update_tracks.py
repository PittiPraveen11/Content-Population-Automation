import json
import http.client
import time
import os
import ssl

# --- CONFIGURATION ---
ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Nzc3MjQxMjQsInVzZXJfbmFtZSI6IjEiLCJhdXRob3JpdGllcyI6WyJST0xFX0REQVBQX1VTRVIiLCJST0xFX0RJVklORV9ERVZJQ0VfU1VQUE9SVCIsIlJPTEVfRERfUFVKQV9DQVNISUVSIiwiUk9MRV9ERF9QVUpBX01BTkFHRVIiLCJST0xFX0RJVklORV9GUkFOQ0hJU0VFX0NBU0hJRVIiLCJST0xFX0RJVklORV9URU1QTEVfVklFV19NQU5BR0VSIiwiUk9MRV9ERF9LSVRfQkFDS09GRklDRSIsIlJPTEVfRERfUFVKQV9BRE1JTiIsIlJPTEVfRERBUFBfQURNSU4iLCJST0xFX0RJVklORV9BRE1JTiIsIlJPTEVfRElWSU5FX0ZSQU5DSElTRUVfT1BFUkFUT1IiLCJST0xFX0REQVBQX1NVUFBPUlQiLCJST0xFX0RJVklORV9GUkFOQ0hJU0VFX0FDQ09VTlRBTlQiLCJST0xFX0RJVklORV9GUkFOQ0hJU0VFX01BTkFHRVIiLCJST0xFX0RJVklORV9GUkFOQ0hJU0VFIiwiUk9MRV9EREFQUF9DT05URU5UX01BTkFHRVIiLCJST0xFX0REX1BVSkFfTU9ERVJBVE9SIl0sImp0aSI6InlHOVBHUFBwdmptQWl4Y2ExZU1adFR5Ty1NTSIsImNsaWVudF9pZCI6InRlY2h4ciIsInNjb3BlIjpbImFsbCJdfQ.JUJR082yjBRA8d0uNPcuGauJELbCWInQItpmDwUxhCH4g7Tw4QTR5NQg9ajhbw5F6IbOa7sfwexKCdgojI17lXYFu9tOkdSQ4QnBT28fBJC8S83A-vyFoPCSAkNzrRfiKfWHyJtvsLGmT6wyVC9_J0bEYdiszUNPxfi9j3uJ1z4FN-XLKgIOR9Qm2OHrPdjA4-fUfPsAeOjHqJxnPKg3__PZJFFq1RHIo1lJT-_2wVy2zIUUwu8jUbci9GRjvbLJyvnC8JFgGFyO0x-90iecBqhhPOiXh0NrvEYnTmc9_OvQYsLYLWmCOw9nhSPeTeptDzKJTZSKt_bHT9Vq1vZVxQ"
HOST = "k8uatgateway.techxrdev.in"
INPUT_FILE = "TracksWithExternalTags.json"

# Set DRY_RUN=True to preview requests without sending.
DRY_RUN = False

# Set LIMIT to a number (e.g. 5) to update only a few tracks.
# Set LIMIT=None to process all tracks.
LIMIT = None

# Optional pagination control when running in chunks.
START_INDEX = 0

REQUEST_DELAY_SECONDS = 0.5
# ---------------------

def update_track_request(conn, track_id, payload):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }
    
    # Remove 'id' from the body if it exists, as requested by the user
    if 'id' in payload:
        del payload['id']
        
    data = json.dumps(payload)
    
    endpoint = f"/api/content/shubhdarshan/v1/admin/tracks/{track_id}"
    
    if DRY_RUN:
        return {
            "status": 200,
            "body": "Dry run success",
            "endpoint": f"PUT https://{HOST}{endpoint}",
            "payload_snippet": data[:100] + "..."
        }

    try:
        conn.request("PUT", endpoint, body=data, headers=headers)
        res = conn.getresponse()
        res_data = res.read().decode("utf-8")
        
        if 200 <= res.status < 300:
            return {"status": res.status, "body": res_data, "endpoint": endpoint}
        else:
            return {"status": res.status, "body": res_data, "error": True, "endpoint": endpoint}
    except Exception as e:
        return {"status": "Error", "body": str(e), "error": True, "endpoint": endpoint}

def main():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, INPUT_FILE)
        
        if not os.path.exists(file_path):
            print(f"Error: Input file not found at {file_path}")
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            all_tracks = json.load(f)

        if not isinstance(all_tracks, list):
            print("Error: Input file must contain a JSON array of track payloads.")
            return

        # Slicing and Limiting
        sliced = all_tracks[START_INDEX:]
        tracks_to_process = sliced[:LIMIT] if LIMIT is not None else sliced

        print(f"Input Payloads: {len(all_tracks)}")
        print(f"START_INDEX: {START_INDEX}")
        print(f"LIMIT: {'ALL' if LIMIT is None else LIMIT}")
        print(f"Tracks to process: {len(tracks_to_process)}")
        print(f"DRY_RUN: {DRY_RUN}")

        success_count = 0
        fail_count = 0

        # Create HTTPS connection
        context = ssl.create_default_context()
        conn = http.client.HTTPSConnection(HOST, context=context)

        for i, track in enumerate(tracks_to_process):
            track_id = track.get('id')
            if not track_id:
                print(f"\n[{i + 1}/{len(tracks_to_process)}] Error: Track missing ID. Skipping.")
                fail_count += 1
                continue

            title_en = track.get('thumbnail', {}).get('title', {}).get('en', 'N/A')
            
            # Create a copy so we don't modify the source list during iteration
            payload = json.loads(json.dumps(track))
            
            print(f"\n[{i + 1}/{len(tracks_to_process)}] Updating: {title_en} (ID: {track_id})")
            
            result = update_track_request(conn, track_id, payload)

            if "error" in result:
                fail_count += 1
                print(f"Failed. Endpoint: {result.get('endpoint')}")
                print(f"Status: {result['status']}")
                print(f"Error Body: {result['body']}")
            else:
                success_count += 1
                if DRY_RUN:
                    print(f"DRY RUN SUCCESS.")
                    print(f"Endpoint: {result['endpoint']}")
                else:
                    print(f"Success. Status: {result['status']}")

            if not DRY_RUN and i < len(tracks_to_process) - 1:
                time.sleep(REQUEST_DELAY_SECONDS)

        conn.close()

        print('\n--- SUMMARY ---')
        print(f"Total selected: {len(tracks_to_process)}")
        print(f"Succeeded: {success_count}")
        print(f"Failed: {fail_count}")
        if DRY_RUN:
            print("\n!!! THIS WAS A DRY RUN. No tracks were actually updated. !!!")
            print("Set DRY_RUN = False in the script to perform live updates.")

    except Exception as e:
        print(f"Critical Error: {str(e)}")

if __name__ == "__main__":
    main()

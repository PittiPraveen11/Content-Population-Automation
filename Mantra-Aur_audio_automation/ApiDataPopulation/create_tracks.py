# import json
# import http.client
# import time
# import os
# import ssl

# # --- CONFIGURATION ---
# ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Nzc3MjQxMjQsInVzZXJfbmFtZSI6IjEiLCJhdXRob3JpdGllcyI6WyJST0xFX0REQVBQX1VTRVIiLCJST0xFX0RJVklORV9ERVZJQ0VfU1VQUE9SVCIsIlJPTEVfRERfUFVKQV9DQVNISUVSIiwiUk9MRV9ERF9QVUpBX01BTkFHRVIiLCJST0xFX0RJVklORV9GUkFOQ0hJU0VFX0NBU0hJRVIiLCJST0xFX0RJVklORV9URU1QTEVfVklFV19NQU5BR0VSIiwiUk9MRV9ERF9LSVRfQkFDS09GRklDRSIsIlJPTEVfRERfUFVKQV9BRE1JTiIsIlJPTEVfRERBUFBfQURNSU4iLCJST0xFX0RJVklORV9BRE1JTiIsIlJPTEVfRElWSU5FX0ZSQU5DSElTRUVfT1BFUkFUT1IiLCJST0xFX0REQVBQX1NVUFBPUlQiLCJST0xFX0RJVklORV9GUkFOQ0hJU0VFX0FDQ09VTlRBTlQiLCJST0xFX0RJVklORV9GUkFOQ0hJU0VFX01BTkFHRVIiLCJST0xFX0RJVklORV9GUkFOQ0hJU0VFIiwiUk9MRV9EREFQUF9DT05URU5UX01BTkFHRVIiLCJST0xFX0REX1BVSkFfTU9ERVJBVE9SIl0sImp0aSI6InlHOVBHUFBwdmptQWl4Y2ExZU1adFR5Ty1NTSIsImNsaWVudF9pZCI6InRlY2h4ciIsInNjb3BlIjpbImFsbCJdfQ.JUJR082yjBRA8d0uNPcuGauJELbCWInQItpmDwUxhCH4g7Tw4QTR5NQg9ajhbw5F6IbOa7sfwexKCdgojI17lXYFu9tOkdSQ4QnBT28fBJC8S83A-vyFoPCSAkNzrRfiKfWHyJtvsLGmT6wyVC9_J0bEYdiszUNPxfi9j3uJ1z4FN-XLKgIOR9Qm2OHrPdjA4-fUfPsAeOjHqJxnPKg3__PZJFFq1RHIo1lJT-_2wVy2zIUUwu8jUbci9GRjvbLJyvnC8JFgGFyO0x-90iecBqhhPOiXh0NrvEYnTmc9_OvQYsLYLWmCOw9nhSPeTeptDzKJTZSKt_bHT9Vq1vZVxQ"
# HOST = "k8uatgateway.techxrdev.in"
# INPUT_FILE = "CleanTracksDTO.json"

# # Set DRY_RUN=True to preview requests without sending.
# DRY_RUN = False

# # Set LIMIT to a number (e.g. 5) to update only a few tracks.
# # Set LIMIT=None to process all tracks.
# LIMIT = None

# # Optional pagination control when running in chunks.
# START_INDEX = 0

# REQUEST_DELAY_SECONDS = 1
# # ---------------------

# def create_track_request(conn, payload):
#     headers = {
#         'Content-Type': 'application/json',
#         'Authorization': f'Bearer {ACCESS_TOKEN}'
#     }
#     data = json.dumps(payload)
    
#     endpoint = "/api/content/shubhdarshan/v1/admin/tracks"
    
#     if DRY_RUN:
#         return {
#             "status": 200,
#             "body": "Dry run success",
#             "endpoint": f"https://{HOST}{endpoint}",
#             "payload": payload
#         }

#     try:
#         conn.request("POST", endpoint, body=data, headers=headers)
#         res = conn.getresponse()
#         res_data = res.read().decode("utf-8")
        
#         if 200 <= res.status < 300:
#             return {"status": res.status, "body": res_data}
#         else:
#             return {"status": res.status, "body": res_data, "error": True}
#     except Exception as e:
#         return {"status": "Error", "body": str(e), "error": True}

# def main():
#     try:
#         # Resolve path relative to script directory
#         script_dir = os.path.dirname(os.path.abspath(__file__))
#         file_path = os.path.join(script_dir, INPUT_FILE)
        
#         if not os.path.exists(file_path):
#             print(f"Error: Input file not found at {file_path}")
#             return

#         with open(file_path, 'r', encoding='utf-8') as f:
#             all_tracks = json.load(f)

#         if not isinstance(all_tracks, list):
#             print("Error: Input file must contain a JSON array of track payloads.")
#             return

#         # Slicing and Limiting
#         sliced = all_tracks[START_INDEX:]
#         tracks_to_process = sliced[:LIMIT] if LIMIT is not None else sliced

#         print(f"Input Payloads: {len(all_tracks)}")
#         print(f"START_INDEX: {START_INDEX}")
#         print(f"LIMIT: {'ALL' if LIMIT is None else LIMIT}")
#         print(f"Tracks to process: {len(tracks_to_process)}")
#         print(f"DRY_RUN: {DRY_RUN}")

#         success_count = 0
#         fail_count = 0

#         # Create HTTPS connection
#         context = ssl.create_default_context()
#         conn = http.client.HTTPSConnection(HOST, context=context)

#         for i, payload in enumerate(tracks_to_process):
#             title_en = payload.get('thumbnail', {}).get('title', {}).get('en', 'N/A')
#             tags = payload.get('tags', [])
            
#             print(f"\n[{i + 1}/{len(tracks_to_process)}] {title_en} | Tags: {tags}")
#             print(f"Endpoint: POST https://{HOST}/api/content/shubhdarshan/v1/admin/tracks")

#             if DRY_RUN:
#                 print("[DRY RUN] Payload snippet:")
#                 # Show only first bit of payload for brevity in terminal
#                 print(json.dumps(payload, indent=2, ensure_ascii=False))

#             result = create_track_request(conn, payload)

#             if "error" in result:
#                 fail_count += 1
#                 print(f"Failed. Status: {result['status']}")
#                 print(f"Error Body: {result['body']}")
#             else:
#                 success_count += 1
#                 print(f"Success. Status: {result['status']}")
#                 if not DRY_RUN and result.get('body'):
#                     try:
#                         parsed = json.loads(result['body'])
#                         print(f"Response: {json.dumps(parsed, indent=2)}")
#                     except:
#                         print(f"Response: {result['body']}")

#             if not DRY_RUN and i < len(tracks_to_process) - 1:
#                 time.sleep(REQUEST_DELAY_SECONDS)

#         conn.close()

#         print('\n--- SUMMARY ---')
#         print(f"Total selected: {len(tracks_to_process)}")
#         print(f"Succeeded: {success_count}")
#         print(f"Failed: {fail_count}")

#     except Exception as e:
#         print(f"Critical Error: {str(e)}")

# if __name__ == "__main__":
#     main()

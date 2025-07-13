#!/usr/bin/env python3
"""
Demo script for anonymous user functionality
"""

import requests
import json
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def demo_anonymous_functionality(base_url="http://localhost:8000"):
    """Demonstrate anonymous user functionality"""
    print("🎭 CLIP.LRU Anonymous User Demo")
    print("=" * 50)
    
    # Check if anonymous access is enabled
    print("1. Checking anonymous access status...")
    response = requests.get(f"{base_url}/api/auth/status")
    if response.status_code != 200:
        print("❌ Server not available")
        return False
    
    status = response.json()
    if not status.get("anonymous_allowed"):
        print("❌ Anonymous access is disabled")
        return False
    
    print("✅ Anonymous access is enabled")
    
    # Create anonymous session
    print("\n2. Creating anonymous session...")
    response = requests.post(f"{base_url}/api/auth/anonymous")
    if response.status_code != 201:
        print(f"❌ Failed to create anonymous session: {response.text}")
        return False
    
    session_data = response.json()
    session_id = session_data["session_id"]
    user = session_data["user"]
    
    print(f"✅ Anonymous session created")
    print(f"   Session ID: {session_id[:16]}...")
    print(f"   Max clips: {user['max_clips']}")
    print(f"   Storage quota: {user['storage_quota']} bytes")
    
    headers = {"X-Session-Id": session_id}
    
    # Create a text clip
    print("\n3. Creating a text clip...")
    clip_data = {
        "title": "Anonymous Demo Clip",
        "content": "This clip was created by an anonymous user!",
        "clip_type": "text",
        "access_level": "public"
    }
    
    response = requests.post(f"{base_url}/api/clips/", 
                           headers=headers, 
                           json=clip_data)
    
    if response.status_code != 201:
        print(f"❌ Failed to create clip: {response.text}")
        return False
    
    clip = response.json()
    clip_id = clip["id"]
    share_token = clip["share_token"]
    
    print(f"✅ Clip created successfully")
    print(f"   Clip ID: {clip_id}")
    print(f"   Share token: {share_token}")
    
    # Access the clip via share token (no authentication needed)
    print("\n4. Accessing clip via share token (no auth)...")
    response = requests.get(f"{base_url}/api/clips/shared/{share_token}")
    
    if response.status_code != 200:
        print(f"❌ Failed to access shared clip: {response.text}")
        return False
    
    shared_clip = response.json()
    print(f"✅ Shared clip accessed successfully")
    print(f"   Title: {shared_clip['title']}")
    print(f"   Content: {shared_clip['content']}")
    print(f"   Access count: {shared_clip['access_count']}")
    
    # Upload a file
    print("\n5. Uploading a file...")
    file_content = "This is a demo file created by an anonymous user."
    files = {"file": ("demo.txt", file_content, "text/plain")}
    
    response = requests.post(f"{base_url}/api/files/upload",
                           headers=headers,
                           files=files)
    
    if response.status_code != 201:
        print(f"❌ Failed to upload file: {response.text}")
        return False
    
    file_data = response.json()["file"]
    file_id = file_data["id"]
    
    print(f"✅ File uploaded successfully")
    print(f"   File ID: {file_id}")
    print(f"   Original filename: {file_data['original_filename']}")
    print(f"   File size: {file_data['file_size']} bytes")
    
    # List user's clips
    print("\n6. Listing user's clips...")
    response = requests.get(f"{base_url}/api/clips/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to list clips: {response.text}")
        return False
    
    clips_data = response.json()
    print(f"✅ Found {clips_data['total']} clips")
    
    for clip in clips_data["clips"]:
        print(f"   - {clip['title']} (ID: {clip['id']})")
    
    # Pin the clip
    print("\n7. Pinning the clip...")
    response = requests.post(f"{base_url}/api/clips/{clip_id}/pin", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to pin clip: {response.text}")
        return False
    
    print("✅ Clip pinned successfully")
    
    # Show final status
    print("\n8. Final status check...")
    response = requests.get(f"{base_url}/api/auth/status", headers=headers)
    final_status = response.json()
    
    print(f"✅ Session still active")
    print(f"   User ID: {final_status['user']['id']}")
    print(f"   Is anonymous: {final_status['user']['is_anonymous']}")
    print(f"   Created at: {final_status['user']['created_at']}")
    
    print("\n🎉 Anonymous user demo completed successfully!")
    print("\nNote: Anonymous users and their data will be automatically")
    print("cleaned up after the configured expiration time.")
    
    return True


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Demo anonymous user functionality")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Base URL of the CLIP.LRU server")
    
    args = parser.parse_args()
    
    try:
        success = demo_anonymous_functionality(args.url)
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

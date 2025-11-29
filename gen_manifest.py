import json
import os
import urllib.request
import urllib.error
from datetime import datetime

# Configuration
REPO_OWNER = "LILCMU"
REPO_NAME = "gogo7-firmware"
FIRMWARE_DIR = "firmware"
MANIFEST_DIR = "manifest"


def get_all_releases():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"
    print(f"Fetching releases from {url}...")
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        print(f"Error fetching release: {e}")
        return None

def download_file(url, dest_path):
    print(f"Downloading {url} to {dest_path}...")
    try:
        with urllib.request.urlopen(url) as response, open(dest_path, 'wb') as out_file:
            data = response.read()
            out_file.write(data)
        print("Download complete.")
        return True
    except urllib.error.URLError as e:
        print(f"Error downloading file: {e}")
        return False

def gen_manifest():
    releases = get_all_releases()
    if not releases:
        return

    # Find latest stable release
    latest_stable = None
    for release in releases:
        if not release['prerelease']:
            latest_stable = release
            break
    
    if latest_stable:
        print(f"Latest stable version: {latest_stable['tag_name']}")
        with open("tag_latest.txt", "w") as f:
            f.write(f"{latest_stable['tag_name']}\n")
    else:
        print("No stable release found.")

    # Create directories if they don't exist
    if not os.path.exists(FIRMWARE_DIR):
        os.makedirs(FIRMWARE_DIR)
    if not os.path.exists(MANIFEST_DIR):
        os.makedirs(MANIFEST_DIR)

    manifests_data = {
        "Gogoboard 7": [],
        "Co-Processor": [],
        "Preview": []
    }
    kept_files = set()
    kept_manifests = set()

    # Process Latest Stable
    if latest_stable:
        version = latest_stable['tag_name']
        assets = latest_stable['assets']
        s3_asset = None
        c3_tasmota_asset = None
        c3_vernier_asset = None

        for asset in assets:
            if "gogo-firmware-" in asset['name'] and asset['name'].endswith(".factory.bin"):
                s3_asset = asset
            elif "tasmota32c3" in asset['name'] and asset['name'].endswith(".factory.bin"):
                c3_tasmota_asset = asset
            elif "vernier" in asset['name'] and asset['name'].endswith(".factory.bin"):
                c3_vernier_asset = asset

        if s3_asset:
            dest = os.path.join(FIRMWARE_DIR, s3_asset['name'])
            kept_files.add(s3_asset['name'])
            download_file(s3_asset['browser_download_url'], dest)
            
            manifest_filename = f"gogo_s3.manifest.json"
            kept_manifests.add(manifest_filename)
            manifest_path = os.path.join(MANIFEST_DIR, manifest_filename)
            
            manifest_s3 = {
                "name": f"Gogoboard 7 Firmware ({version})",
                "version": version,
                "new_install_prompt_erase": True,
                "builds": [{
                    "chipFamily": "ESP32-S3",
                    "improv": False,
                    "parts": [{ "path": f"../{FIRMWARE_DIR}/{s3_asset['name']}", "offset": 0 }]
                }]
            }
            with open(manifest_path, 'w') as f:
                json.dump(manifest_s3, f, indent=4)
            
            manifests_data["Gogoboard 7"].append({
                "path": f"{MANIFEST_DIR}/{manifest_filename}",
                "name": f"Gogoboard 7 Firmware",
                "chipFamilies": ["ESP32-S3"],
                "features": {}
            })

        if c3_tasmota_asset:
            dest = os.path.join(FIRMWARE_DIR, c3_tasmota_asset['name'])
            kept_files.add(c3_tasmota_asset['name'])
            download_file(c3_tasmota_asset['browser_download_url'], dest)

            manifest_filename = f"gogo_c3_tasmota.manifest.json"
            kept_manifests.add(manifest_filename)
            manifest_path = os.path.join(MANIFEST_DIR, manifest_filename)

            manifest_c3_tasmota = {
                "name": f"Co-Processor Tasmota ({version})",
                "version": version,
                "new_install_prompt_erase": True,
                "builds": [{
                    "chipFamily": "ESP32-C3",
                    "improv": False,
                    "parts": [{ "path": f"../{FIRMWARE_DIR}/{c3_tasmota_asset['name']}", "offset": 0 }]
                }]
            }
            with open(manifest_path, 'w') as f:
                json.dump(manifest_c3_tasmota, f, indent=4)
            
            manifests_data["Co-Processor"].append({
                "path": f"{MANIFEST_DIR}/{manifest_filename}",
                "name": f"Tasmota (C3)",
                "chipFamilies": ["ESP32-C3"],
                "features": {}
            })

        if c3_vernier_asset:
            dest = os.path.join(FIRMWARE_DIR, c3_vernier_asset['name'])
            kept_files.add(c3_vernier_asset['name'])
            download_file(c3_vernier_asset['browser_download_url'], dest)

            manifest_filename = f"gogo_c3_vernier.manifest.json"
            kept_manifests.add(manifest_filename)
            manifest_path = os.path.join(MANIFEST_DIR, manifest_filename)

            manifest_c3_vernier = {
                "name": f"Co-Processor Vernier ({version})",
                "version": version,
                "new_install_prompt_erase": True,
                "builds": [{
                    "chipFamily": "ESP32-C3",
                    "improv": False,
                    "parts": [{ "path": f"../{FIRMWARE_DIR}/{c3_vernier_asset['name']}", "offset": 0 }]
                }]
            }
            with open(manifest_path, 'w') as f:
                json.dump(manifest_c3_vernier, f, indent=4)
            
            manifests_data["Co-Processor"].append({
                "path": f"{MANIFEST_DIR}/{manifest_filename}",
                "name": f"Vernier (C3)",
                "chipFamilies": ["ESP32-C3"],
                "features": {}
            })

    # Process Pre-releases
    for release in releases:
        if not release['prerelease']:
            continue
            
        version = release['tag_name']
        print(f"Processing pre-release: {version}")
        
        assets = release['assets']
        # Sort assets: gogo-firmware* first, then others
        assets.sort(key=lambda x: 0 if x['name'].startswith("gogo-firmware") else 1)
        
        for asset in assets:
            if not asset['name'].endswith(".bin"):
                continue

            dest = os.path.join(FIRMWARE_DIR, asset['name'])
            kept_files.add(asset['name'])
            download_file(asset['browser_download_url'], dest)
            
            # Determine chip family (default to ESP32-S3 if unknown, or try to guess)
            # For now, let's assume ESP32-S3 for generic bins unless C3 is in name
            chip_family = "ESP32-S3"
            name_ext = ""
            if "c3" in asset['name'].lower() or "-co-" in asset['name'].lower():
                chip_family = "ESP32-C3"
                name_ext = " (C3)"
            
            manifest_filename = f"preview_{version}_{asset['name']}.manifest.json"
            kept_manifests.add(manifest_filename)
            manifest_path = os.path.join(MANIFEST_DIR, manifest_filename)
            
            manifest_data = {
                "name": f"{asset['name']} ({version})",
                "version": version,
                "new_install_prompt_erase": True,
                "builds": [{
                    "chipFamily": chip_family,
                    "improv": False,
                    "parts": [{ "path": f"../{FIRMWARE_DIR}/{asset['name']}", "offset": 0 }]
                }]
            }
            with open(manifest_path, 'w') as f:
                json.dump(manifest_data, f, indent=4)
            
            manifests_data["Preview"].append({
                "path": f"{MANIFEST_DIR}/{manifest_filename}",
                "name": f"{release['name']} {name_ext}",
                "chipFamilies": [chip_family],
                "features": {}
            })

    # Cleanup unrelated files
    print("Cleaning up unrelated firmware files...")
    for filename in os.listdir(FIRMWARE_DIR):
        if filename not in kept_files:
            file_path = os.path.join(FIRMWARE_DIR, filename)
            try:
                os.remove(file_path)
                print(f"Deleted {filename}")
            except OSError as e:
                print(f"Error deleting {filename}: {e}")

    print("Cleaning up unrelated manifest files...")
    for filename in os.listdir(MANIFEST_DIR):
        if filename not in kept_manifests:
            file_path = os.path.join(MANIFEST_DIR, filename)
            try:
                os.remove(file_path)
                print(f"Deleted {filename}")
            except OSError as e:
                print(f"Error deleting {filename}: {e}")

    # Write manifests.json
    with open("manifests.json", 'w') as f:
        json.dump(manifests_data, f, indent=4)
    print("Generated manifests.json")

if __name__ == "__main__":
    gen_manifest()

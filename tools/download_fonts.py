"""Download font files from Google Fonts for text injection."""

import os
import sys
import urllib.request
import zipfile
import io
import shutil

FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts")

GOOGLE_FONTS = {
    "Liberation Sans": {
        "url": "https://github.com/liberationfonts/liberation-fonts/files/7261482/liberation-fonts-ttf-2.1.5.tar.gz",
        "type": "tar.gz",
        "files": {
            "LiberationSans-Regular.ttf": "liberation-fonts-ttf-2.1.5/LiberationSans-Regular.ttf",
        },
    },
    "Courier Prime": {
        "url": "https://fonts.google.com/download?family=Courier+Prime",
        "type": "zip",
        "files": {
            "CourierPrime-Regular.ttf": "CourierPrime-Regular.ttf",
        },
    },
    "Open Sans": {
        "url": "https://fonts.google.com/download?family=Open+Sans",
        "type": "zip",
        "files": {
            "OpenSans-Regular.ttf": None,  # Search for it in the zip
        },
    },
}

# Direct URLs that are more reliable
DIRECT_FONT_URLS = [
    (
        "LiberationSans-Regular.ttf",
        "https://github.com/liberationfonts/liberation-fonts/raw/main/liberation-fonts-ttf-2.1.5/LiberationSans-Regular.ttf",
    ),
    (
        "CourierPrime-Regular.ttf",
        "https://raw.githubusercontent.com/quoteunquoteapps/CourierPrime/master/fonts/ttf/CourierPrime-Regular.ttf",
    ),
    (
        "OpenSans-Regular.ttf",
        "https://github.com/google/fonts/raw/main/ofl/opensans/OpenSans%5Bwdth%2Cwght%5D.ttf",
    ),
]

# Fallback: bundled with many systems
SYSTEM_FONT_SEARCH_PATHS = [
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    os.path.expanduser("~/Library/Fonts"),
    "/Library/Fonts",
    "/System/Library/Fonts",
]


def download_font(name: str, url: str, dest_path: str) -> bool:
    """Download a single font file."""
    if os.path.exists(dest_path):
        print(f"  Already exists: {dest_path}")
        return True
    try:
        print(f"  Downloading {name} from {url[:80]}...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        with open(dest_path, "wb") as f:
            f.write(data)
        print(f"  Saved: {dest_path} ({len(data)} bytes)")
        return True
    except Exception as e:
        print(f"  Failed to download {name}: {e}")
        return False


def find_system_font(name_pattern: str) -> str | None:
    """Search system font directories for a matching font file."""
    import fnmatch

    for search_dir in SYSTEM_FONT_SEARCH_PATHS:
        if not os.path.isdir(search_dir):
            continue
        for root, _dirs, files in os.walk(search_dir):
            for f in files:
                if fnmatch.fnmatch(f.lower(), name_pattern.lower()):
                    return os.path.join(root, f)
    return None


def download_from_zip(url: str, target_filename: str, dest_path: str) -> bool:
    """Download a zip and extract a specific font file."""
    if os.path.exists(dest_path):
        print(f"  Already exists: {dest_path}")
        return True
    try:
        print(f"  Downloading zip from {url[:80]}...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            # Find the target file in the zip
            for zi in zf.infolist():
                if zi.filename.endswith(target_filename) or target_filename in zi.filename:
                    with zf.open(zi) as src, open(dest_path, "wb") as dst:
                        dst.write(src.read())
                    print(f"  Extracted: {dest_path}")
                    return True
        print(f"  Could not find {target_filename} in zip")
        return False
    except Exception as e:
        print(f"  Failed: {e}")
        return False


def main():
    os.makedirs(FONTS_DIR, exist_ok=True)

    required_fonts = [
        "LiberationSans-Regular.ttf",
        "CourierPrime-Regular.ttf",
        "OpenSans-Regular.ttf",
    ]

    success_count = 0

    print("Downloading fonts for formation document generator...\n")

    # Try direct downloads first
    for font_name, url in DIRECT_FONT_URLS:
        dest = os.path.join(FONTS_DIR, font_name)
        if download_font(font_name, url, dest):
            success_count += 1
        else:
            # Try to find on system
            print(f"  Searching system fonts for {font_name}...")
            system_path = find_system_font(font_name)
            if system_path:
                shutil.copy2(system_path, dest)
                print(f"  Copied from system: {system_path}")
                success_count += 1
            else:
                print(f"  WARNING: Could not obtain {font_name}")

    print(f"\nResults: {success_count}/{len(required_fonts)} fonts available")

    # Verify
    missing = []
    for font_name in required_fonts:
        path = os.path.join(FONTS_DIR, font_name)
        if not os.path.exists(path):
            missing.append(font_name)

    if missing:
        print(f"\nMissing fonts: {', '.join(missing)}")
        print("Please download these manually and place them in the fonts/ directory.")
        print("Sources:")
        print("  - Liberation Sans: https://github.com/liberationfonts/liberation-fonts/releases")
        print("  - Courier Prime: https://fonts.google.com/specimen/Courier+Prime")
        print("  - Open Sans: https://fonts.google.com/specimen/Open+Sans")
        return 1

    print("\nAll fonts ready!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

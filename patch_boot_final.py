import os
import re
import sys

# Patch to disable pkg_resources in __boot__.py and fix ffmpeg permissions

boot_file = "dist/xScribe.app/Contents/Resources/__boot__.py"
ffmpeg_path = "dist/xScribe.app/Contents/Resources/bin/ffmpeg"

print(f"Patching {boot_file}...")

try:
    with open(boot_file, "r") as f:
        content = f.read()

    # 1. Comment out the import (exact match)
    content = content.replace(
        "import pkg_resources, zipimport, os",
        "# import pkg_resources, zipimport, os  # DISABLED\nimport zipimport, os",
    )

    # 2. Comment out the function CALL (not the definition)
    # Use regex to match the call precisely (standalone line)
    content = re.sub(
        r"^(_fixup_pkg_resources\(\))$",
        r"# \1  # DISABLED",
        content,
        flags=re.MULTILINE,
    )

    # Write back
    with open(boot_file, "w") as f:
        f.write(content)

    print("Patched successfully")

    import py_compile

    py_compile.compile(boot_file, doraise=True)
    print("Python syntax is valid")

    print(f"\nFixing ffmpeg permissions at {ffmpeg_path}...")
    if os.path.exists(ffmpeg_path):
        # Make ffmpeg executable (0o755 = rwxr-xr-x)
        os.chmod(ffmpeg_path, 0o755)
        print("ffmpeg is now executable")
    else:
        print(f"Warning: ffmpeg not found at {ffmpeg_path}")

    print("\nReady to test!")

except Exception as e:
    print(f"Failed: {e}")
    sys.exit(1)

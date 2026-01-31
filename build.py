#!/usr/bin/env python3
"""
Build script for packaging DiceAutoApply as a standalone application
Supports macOS (.app bundle) and Windows (.exe)
"""

import os
import sys
import platform
import shutil
import subprocess
from pathlib import Path


def get_platform():
    """Get the current platform."""
    system = platform.system()
    if system == "Darwin":
        return "macos"
    elif system == "Windows":
        return "windows"
    elif system == "Linux":
        return "linux"
    else:
        return system.lower()


def ensure_pyinstaller():
    """Ensure PyInstaller is installed."""
    try:
        import PyInstaller
        print(f"PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller>=6.0.0"])


def clean_build():
    """Clean previous build artifacts."""
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        path = Path(dir_name)
        if path.exists():
            print(f"Cleaning {dir_name}/")
            shutil.rmtree(path)

    # Clean .spec files
    for spec_file in Path(".").glob("*.spec"):
        print(f"Removing {spec_file}")
        spec_file.unlink()


def create_icon():
    """Create a simple icon if none exists."""
    icons_dir = Path("assets")
    icons_dir.mkdir(exist_ok=True)

    # Check if icons exist
    icns_path = icons_dir / "icon.icns"
    ico_path = icons_dir / "icon.ico"
    png_path = icons_dir / "icon.png"

    if not any([icns_path.exists(), ico_path.exists(), png_path.exists()]):
        print("Note: No icon files found in assets/")
        print("  - For macOS: Create assets/icon.icns")
        print("  - For Windows: Create assets/icon.ico")
        print("  - Building without custom icon...")
        return None

    current_platform = get_platform()
    if current_platform == "macos" and icns_path.exists():
        return str(icns_path)
    elif current_platform == "windows" and ico_path.exists():
        return str(ico_path)
    elif png_path.exists():
        return str(png_path)

    return None


def build_macos():
    """Build macOS .app bundle."""
    print("\n=== Building for macOS ===\n")

    icon = create_icon()
    icon_arg = f"--icon={icon}" if icon else ""

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=DiceAutoApply",
        "--windowed",
        "--onedir",
        "--noconfirm",
        "--clean",
        "--add-data=assets:assets",
        "--add-data=config:config",
        "--hidden-import=flet",
        "--hidden-import=flet_core",
        "--hidden-import=flet_runtime",
        "--hidden-import=schedule",
        "--hidden-import=keyring",
        "--hidden-import=keyring.backends",
        "--hidden-import=keyring.backends.macOS",
        "--collect-all=flet",
        "--collect-all=flet_core",
        "--collect-all=flet_runtime",
        "--osx-bundle-identifier=com.diceautoapply.app",
        "src/main.py",
    ]

    if icon_arg:
        cmd.insert(-1, icon_arg)

    print("Running PyInstaller...")
    print(" ".join(cmd))

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n=== Build Successful ===")
        print(f"Output: dist/DiceAutoApply.app")

        # Create DMG (optional)
        try:
            create_dmg()
        except Exception as e:
            print(f"Note: Could not create DMG: {e}")

        return True
    else:
        print("\n=== Build Failed ===")
        return False


def build_windows():
    """Build Windows .exe."""
    print("\n=== Building for Windows ===\n")

    icon = create_icon()
    icon_arg = f"--icon={icon}" if icon else ""

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=DiceAutoApply",
        "--windowed",
        "--onedir",
        "--noconfirm",
        "--clean",
        "--add-data=assets;assets",
        "--add-data=config;config",
        "--hidden-import=flet",
        "--hidden-import=flet_core",
        "--hidden-import=flet_runtime",
        "--hidden-import=schedule",
        "--hidden-import=keyring",
        "--hidden-import=keyring.backends",
        "--hidden-import=keyring.backends.Windows",
        "--collect-all=flet",
        "--collect-all=flet_core",
        "--collect-all=flet_runtime",
        "src/main.py",
    ]

    if icon_arg:
        cmd.insert(-1, icon_arg)

    print("Running PyInstaller...")
    print(" ".join(cmd))

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n=== Build Successful ===")
        print(f"Output: dist/DiceAutoApply/DiceAutoApply.exe")
        return True
    else:
        print("\n=== Build Failed ===")
        return False


def build_linux():
    """Build Linux executable."""
    print("\n=== Building for Linux ===\n")

    icon = create_icon()
    icon_arg = f"--icon={icon}" if icon else ""

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=DiceAutoApply",
        "--windowed",
        "--onedir",
        "--noconfirm",
        "--clean",
        "--add-data=assets:assets",
        "--add-data=config:config",
        "--hidden-import=flet",
        "--hidden-import=flet_core",
        "--hidden-import=flet_runtime",
        "--hidden-import=schedule",
        "--hidden-import=keyring",
        "--hidden-import=keyring.backends",
        "--collect-all=flet",
        "--collect-all=flet_core",
        "--collect-all=flet_runtime",
        "src/main.py",
    ]

    if icon_arg:
        cmd.insert(-1, icon_arg)

    print("Running PyInstaller...")
    print(" ".join(cmd))

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n=== Build Successful ===")
        print(f"Output: dist/DiceAutoApply/DiceAutoApply")
        return True
    else:
        print("\n=== Build Failed ===")
        return False


def create_dmg():
    """Create macOS DMG file."""
    app_path = Path("dist/DiceAutoApply.app")
    dmg_path = Path("dist/DiceAutoApply.dmg")

    if not app_path.exists():
        return

    print("\nCreating DMG...")

    # Remove existing DMG
    if dmg_path.exists():
        dmg_path.unlink()

    # Create DMG using hdiutil
    cmd = [
        "hdiutil", "create",
        "-volname", "DiceAutoApply",
        "-srcfolder", str(app_path),
        "-ov",
        "-format", "UDZO",
        str(dmg_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"DMG created: {dmg_path}")
    else:
        print(f"Failed to create DMG: {result.stderr}")


def main():
    """Main build function."""
    import argparse

    parser = argparse.ArgumentParser(description="Build DiceAutoApply application")
    parser.add_argument(
        "--platform",
        choices=["macos", "windows", "linux", "auto"],
        default="auto",
        help="Target platform (default: auto-detect)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts before building",
    )
    parser.add_argument(
        "--clean-only",
        action="store_true",
        help="Only clean build artifacts, don't build",
    )

    args = parser.parse_args()

    # Change to project root directory
    os.chdir(Path(__file__).parent)

    if args.clean or args.clean_only:
        clean_build()
        if args.clean_only:
            return

    ensure_pyinstaller()

    # Ensure required directories exist
    Path("assets").mkdir(exist_ok=True)
    Path("config").mkdir(exist_ok=True)

    # Determine platform
    target_platform = args.platform
    if target_platform == "auto":
        target_platform = get_platform()

    print(f"Building for platform: {target_platform}")

    # Build
    if target_platform == "macos":
        success = build_macos()
    elif target_platform == "windows":
        success = build_windows()
    elif target_platform == "linux":
        success = build_linux()
    else:
        print(f"Unsupported platform: {target_platform}")
        success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

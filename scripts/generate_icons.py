"""
Generate placeholder app icons for DiceAutoApply
Run this script to create icon.png, icon.icns (macOS), and icon.ico (Windows)
"""

import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("PIL not available. Install with: pip install Pillow")

# Colors from the app's color scheme
BACKGROUND = (26, 26, 46)  # #1a1a2e
ACCENT = (233, 69, 96)      # #e94560
TEXT = (255, 255, 255)      # #ffffff


def create_icon_image(size: int = 512) -> "Image":
    """Create a simple icon image."""
    if not HAS_PIL:
        return None

    # Create base image
    img = Image.new("RGBA", (size, size), BACKGROUND)
    draw = ImageDraw.Draw(img)

    # Draw a rounded rectangle background
    margin = size // 10
    radius = size // 6

    # Draw accent colored dice-like shape
    center = size // 2
    dice_size = size // 2

    # Draw a tilted square (dice)
    offset = dice_size // 2
    points = [
        (center, center - offset),          # top
        (center + offset, center),          # right
        (center, center + offset),          # bottom
        (center - offset, center),          # left
    ]
    draw.polygon(points, fill=ACCENT)

    # Draw dots on the dice (like a 4)
    dot_radius = size // 20
    dot_offset = dice_size // 4

    dot_positions = [
        (center - dot_offset // 2, center - dot_offset // 2),
        (center + dot_offset // 2, center - dot_offset // 2),
        (center - dot_offset // 2, center + dot_offset // 2),
        (center + dot_offset // 2, center + dot_offset // 2),
    ]

    for x, y in dot_positions:
        draw.ellipse(
            [x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius],
            fill=TEXT
        )

    # Draw "D" letter for Dice
    try:
        # Try to use a system font
        font_size = size // 4
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except OSError:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except OSError:
                font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    return img


def create_icns(png_path: Path, icns_path: Path):
    """Create macOS .icns file from PNG."""
    if not HAS_PIL:
        return False

    try:
        # Create iconset directory
        iconset_dir = png_path.parent / "icon.iconset"
        iconset_dir.mkdir(exist_ok=True)

        # Required sizes for iconset
        sizes = [16, 32, 64, 128, 256, 512]

        img = Image.open(png_path)

        for size in sizes:
            # Standard resolution
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            resized.save(iconset_dir / f"icon_{size}x{size}.png")

            # High resolution (@2x)
            if size <= 256:
                resized_2x = img.resize((size * 2, size * 2), Image.Resampling.LANCZOS)
                resized_2x.save(iconset_dir / f"icon_{size}x{size}@2x.png")

        # Convert iconset to icns using iconutil (macOS only)
        import subprocess
        result = subprocess.run(
            ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(icns_path)],
            capture_output=True,
            text=True
        )

        # Clean up iconset directory
        import shutil
        shutil.rmtree(iconset_dir, ignore_errors=True)

        return result.returncode == 0
    except Exception as e:
        print(f"Failed to create .icns: {e}")
        return False


def create_ico(png_path: Path, ico_path: Path):
    """Create Windows .ico file from PNG."""
    if not HAS_PIL:
        return False

    try:
        img = Image.open(png_path)

        # ICO sizes
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

        # Create multiple sizes
        icons = []
        for size in sizes:
            resized = img.resize(size, Image.Resampling.LANCZOS)
            icons.append(resized)

        # Save as ICO
        icons[0].save(
            ico_path,
            format="ICO",
            sizes=sizes,
            append_images=icons[1:]
        )
        return True
    except Exception as e:
        print(f"Failed to create .ico: {e}")
        return False


def main():
    """Generate all icon files."""
    # Determine paths
    script_dir = Path(__file__).parent
    assets_dir = script_dir.parent / "assets"
    assets_dir.mkdir(exist_ok=True)

    png_path = assets_dir / "icon.png"
    icns_path = assets_dir / "icon.icns"
    ico_path = assets_dir / "icon.ico"

    if not HAS_PIL:
        print("Please install Pillow first: pip install Pillow")
        return

    print("Generating app icons...")

    # Create PNG
    img = create_icon_image(512)
    if img:
        img.save(png_path, "PNG")
        print(f"Created: {png_path}")

        # Create ICO for Windows
        if create_ico(png_path, ico_path):
            print(f"Created: {ico_path}")
        else:
            print("Could not create .ico file")

        # Create ICNS for macOS (only works on macOS)
        import platform
        if platform.system() == "Darwin":
            if create_icns(png_path, icns_path):
                print(f"Created: {icns_path}")
            else:
                print("Could not create .icns file (iconutil may not be available)")
        else:
            print("Skipping .icns creation (not on macOS)")

    print("Done!")


if __name__ == "__main__":
    main()

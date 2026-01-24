#!/usr/bin/env python3
"""
Simple script to create placeholder PWA icons
Run with: python3 scripts/create-icons.py
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, output_path):
    """Create a simple green icon with 'MP' text"""
    # Create a green square image
    img = Image.new('RGB', (size, size), color='#16a34a')
    draw = ImageDraw.Draw(img)
    
    # Try to use a font, fallback to default if not available
    try:
        # Try to use a system font
        font_size = size // 4
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        try:
            font = ImageFont.load_default()
        except:
            font = None
    
    # Draw 'MP' text in the center
    text = "MP"
    if font:
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    else:
        # Estimate size if no font
        text_width = size // 3
        text_height = size // 4
    
    # Center the text
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    
    draw.text((x, y), text, fill='white', font=font)
    
    # Save as PNG
    img.save(output_path, 'PNG')
    print(f"✅ Created {size}x{size} icon: {output_path}")

if __name__ == '__main__':
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("❌ PIL (Pillow) not installed. Installing...")
        print("Run: pip3 install Pillow")
        print("\nOr use an online tool to create icons:")
        print("1. Go to https://realfavicongenerator.net/")
        print("2. Upload icon.svg")
        print("3. Download the generated icons")
        print("4. Place in frontend/public/")
        exit(1)
    
    # Create public directory if it doesn't exist
    public_dir = os.path.join(os.path.dirname(__file__), '../public')
    os.makedirs(public_dir, exist_ok=True)
    
    # Create icons
    create_icon(192, os.path.join(public_dir, 'icon-192x192.png'))
    create_icon(512, os.path.join(public_dir, 'icon-512x512.png'))
    
    print("\n✅ All icons created successfully!")

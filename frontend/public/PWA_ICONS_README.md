# PWA Icons Setup

This app requires two icon sizes for PWA functionality:
- `icon-192x192.png` (192x192 pixels)
- `icon-512x512.png` (512x512 pixels)

## Quick Setup

### Option 1: Use an Online Icon Generator
1. Create or find a logo/image for the Masters Pool
2. Use an online tool like:
   - https://realfavicongenerator.net/
   - https://www.pwabuilder.com/imageGenerator
   - https://favicon.io/
3. Upload your image and generate the required sizes
4. Download and place in `/frontend/public/` directory

### Option 2: Create Icons Manually
1. Create a square image (at least 512x512 pixels)
2. Use image editing software to resize:
   - 192x192 pixels → `icon-192x192.png`
   - 512x512 pixels → `icon-512x512.png`
3. Ensure icons are PNG format with transparency support
4. Place both files in `/frontend/public/` directory

### Option 3: Use a Simple Placeholder (Temporary)
For development, you can create simple colored squares:

```bash
# Using ImageMagick (if installed)
convert -size 192x192 xc:#16a34a frontend/public/icon-192x192.png
convert -size 512x512 xc:#16a34a frontend/public/icon-512x512.png
```

Or use any image editor to create green squares with the text "MP" or a golf-related icon.

## Icon Requirements

- **Format**: PNG
- **Sizes**: 192x192 and 512x512 pixels
- **Purpose**: Should work as "any" and "maskable"
- **Design**: Should be recognizable at small sizes
- **Background**: Transparent or solid color

## Testing

After adding icons:
1. Build the app: `npm run build`
2. Check that icons appear in `/dist/` directory
3. Test PWA installation in browser
4. Verify icons appear correctly when installed

## Notes

- Icons are referenced in `manifest.json`
- Icons should be optimized for file size
- Consider using SVG source and converting to PNG for best quality

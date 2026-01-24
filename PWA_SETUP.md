# PWA Setup Guide

This guide explains how to set up the Progressive Web App (PWA) features that have been implemented.

## What's Been Implemented

✅ **Web App Manifest** - App can be installed on devices
✅ **Service Worker** - Offline support and caching
✅ **Install Prompt** - Custom prompt to install the app
✅ **Push Notification Support** - Ready for push notifications (backend integration needed)

## Setup Steps

### 1. Create App Icons

The app needs two icon files in `frontend/public/`:
- `icon-192x192.png` (192x192 pixels)
- `icon-512x512.png` (512x512 pixels)

**Option A: Use the SVG Template**
1. Open `frontend/public/icon.svg` in an image editor
2. Export as PNG at 192x192 and 512x512 sizes
3. Save as `icon-192x192.png` and `icon-512x512.png` in `frontend/public/`

**Option B: Use Online Tool**
1. Go to https://realfavicongenerator.net/ or https://www.pwabuilder.com/imageGenerator
2. Upload your logo/image
3. Generate and download the required sizes
4. Place in `frontend/public/`

**Option C: Quick Placeholder (Development)**
```bash
# Using ImageMagick (if installed)
convert -size 192x192 xc:#16a34a -pointsize 48 -fill white -gravity center -annotate +0+0 "MP" frontend/public/icon-192x192.png
convert -size 512x512 xc:#16a34a -pointsize 128 -fill white -gravity center -annotate +0+0 "MP" frontend/public/icon-512x512.png
```

### 2. Build and Deploy

The PWA features are automatically included when you build:

```bash
cd frontend
npm run build
```

The service worker and manifest will be included in the `dist/` directory.

### 3. Test PWA Features

#### Test Installation
1. Open the app in Chrome (Android or Desktop)
2. Look for the install prompt or use browser menu
3. Click "Install" to add to home screen
4. Verify the app opens in standalone mode

#### Test Offline Support
1. Install the app
2. Open the app
3. Turn off internet/airplane mode
4. Navigate the app - cached pages should still work
5. API calls will show "Offline - No cached data available" message

#### Test Service Worker
1. Open Chrome DevTools → Application tab
2. Check "Service Workers" section
3. Verify service worker is registered and active
4. Check "Cache Storage" to see cached files

### 4. Push Notifications (Future)

Push notifications are set up in the service worker but need backend integration:

1. Set up VAPID keys for web push
2. Create push notification subscription endpoint
3. Store subscription tokens in database
4. Send notifications from backend when events occur

## Features

### ✅ Currently Working

- **Installable**: App can be added to home screen
- **Offline Viewing**: Cached pages work offline
- **App-like Experience**: Standalone mode, no browser UI
- **Install Prompt**: Custom prompt appears when installable

### 🚧 Ready but Needs Backend

- **Push Notifications**: Service worker ready, needs backend integration
- **Background Sync**: Service worker ready, needs implementation

## Browser Support

- ✅ **Chrome** (Android & Desktop): Full support
- ✅ **Edge**: Full support
- ✅ **Firefox**: Full support
- ⚠️ **Safari iOS 16.4+**: Limited support (push notifications work)
- ⚠️ **Safari iOS < 16.4**: Basic support (no push notifications)

## Troubleshooting

### Service Worker Not Registering
- Check browser console for errors
- Ensure app is served over HTTPS (or localhost)
- Clear browser cache and reload

### Icons Not Showing
- Verify icons exist in `frontend/public/`
- Check that icons are referenced in `manifest.json`
- Rebuild the app after adding icons

### Install Prompt Not Showing
- Only shows on supported browsers (Chrome, Edge)
- Only shows if app meets PWA criteria
- Check browser console for errors

### Offline Not Working
- Verify service worker is active in DevTools
- Check cache storage in DevTools
- Ensure pages were visited while online

## Next Steps

1. **Add Icons**: Create and add the required icon files
2. **Test Installation**: Test on various devices and browsers
3. **Push Notifications**: Integrate backend push notification service
4. **Monitor**: Check service worker registration in production
5. **Gather Feedback**: See how users respond to PWA features

## Safety Features

- ✅ Service worker only registers in production (`import.meta.env.PROD`)
- ✅ Graceful degradation if service worker fails
- ✅ No breaking changes to existing functionality
- ✅ Backwards compatible with all browsers

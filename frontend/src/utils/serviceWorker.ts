/**
 * Service Worker Registration
 * Handles registration and updates of the service worker for PWA functionality
 */

export function registerServiceWorker(): void {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      const swUrl = '/service-worker.js';

      navigator.serviceWorker
        .register(swUrl)
        .then((registration) => {
          console.log('[PWA] Service Worker registered:', registration);

          // Check for updates periodically
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            if (newWorker) {
              newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                  // New service worker available
                  console.log('[PWA] New service worker available');
                  // Optionally show update notification to user
                }
              });
            }
          });
        })
        .catch((error) => {
          console.error('[PWA] Service Worker registration failed:', error);
        });

      // Check for service worker updates
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        console.log('[PWA] Service Worker controller changed - reloading page');
        // Optionally reload the page to get the new service worker
        // window.location.reload();
      });
    });
  } else {
    console.log('[PWA] Service Workers are not supported in this browser');
  }
}

export function unregisterServiceWorker(): void {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready.then((registration) => {
      registration.unregister().then((success) => {
        if (success) {
          console.log('[PWA] Service Worker unregistered');
        }
      });
    });
  }
}

/**
 * Check if the app is running as a PWA (installed)
 */
export function isPWAInstalled(): boolean {
  if (typeof window === 'undefined') return false;
  
  // Check if running in standalone mode (iOS)
  if ((window.navigator as any).standalone) {
    return true;
  }
  
  // Check if running in standalone mode (Android/Chrome)
  if (window.matchMedia('(display-mode: standalone)').matches) {
    return true;
  }
  
  return false;
}

/**
 * Show install prompt (if available)
 */
export async function showInstallPrompt(): Promise<boolean> {
  // Check if beforeinstallprompt event is supported
  if ('serviceWorker' in navigator && 'BeforeInstallPromptEvent' in window) {
    // This will be handled by the beforeinstallprompt event listener
    return true;
  }
  return false;
}

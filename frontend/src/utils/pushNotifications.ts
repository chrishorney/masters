/**
 * Push notification utilities
 */

export interface PushSubscriptionData {
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
}

/**
 * Request notification permission
 */
export async function requestNotificationPermission(): Promise<NotificationPermission> {
  if (!('Notification' in window)) {
    console.log('This browser does not support notifications');
    return 'denied';
  }

  if (Notification.permission === 'granted') {
    return 'granted';
  }

  if (Notification.permission !== 'denied') {
    const permission = await Notification.requestPermission();
    return permission;
  }

  return Notification.permission;
}

/**
 * Get VAPID public key from server
 */
export async function getVAPIDPublicKey(): Promise<string> {
  try {
    // Use the same API URL configuration as the rest of the app
    const API_URL = import.meta.env.VITE_API_URL || '';
    const API_PREFIX = '/api';
    const baseURL = API_URL ? `${API_URL}${API_PREFIX}` : API_PREFIX;
    
    const response = await fetch(`${baseURL}/push/public-key`);
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to get VAPID public key: ${response.status} ${errorText}`);
    }
    const data = await response.json();
    return data.publicKey;
  } catch (error: any) {
    console.error('Error getting VAPID public key:', error);
    throw error;
  }
}

/**
 * Convert VAPID key from base64 URL to Uint8Array
 */
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

/**
 * Convert ArrayBuffer to base64
 */
function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}

/**
 * Subscribe to push notifications
 */
export async function subscribeToPushNotifications(): Promise<PushSubscriptionData | null> {
  try {
    // Check if service worker is supported
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      const error = 'Push notifications are not supported in this browser';
      console.error(error);
      throw new Error(error);
    }

    // Request permission
    const permission = await requestNotificationPermission();
    if (permission !== 'granted') {
      const error = `Notification permission ${permission}. Please enable notifications in your browser settings.`;
      console.error(error);
      throw new Error(error);
    }

    // Get VAPID public key
    let publicKey: string;
    try {
      publicKey = await getVAPIDPublicKey();
      console.log('VAPID public key retrieved:', publicKey.substring(0, 20) + '...');
    } catch (error: any) {
      const errorMsg = `Failed to get VAPID public key: ${error.message || error}`;
      console.error(errorMsg);
      throw new Error(errorMsg);
    }
    
    // Convert VAPID key to Uint8Array
    let applicationServerKey: Uint8Array;
    try {
      applicationServerKey = urlBase64ToUint8Array(publicKey);
      console.log('VAPID key converted to Uint8Array, length:', applicationServerKey.length);
    } catch (error: any) {
      const errorMsg = `Failed to convert VAPID key: ${error.message || error}`;
      console.error(errorMsg);
      throw new Error(errorMsg);
    }

    // Register service worker
    let registration: ServiceWorkerRegistration;
    try {
      registration = await navigator.serviceWorker.ready;
      console.log('Service worker ready, scope:', registration.scope);
    } catch (error: any) {
      const errorMsg = `Service worker not ready: ${error.message || error}`;
      console.error(errorMsg);
      throw new Error(errorMsg);
    }

    // Subscribe to push
    let subscription: PushSubscription;
    try {
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: applicationServerKey as unknown as ArrayBuffer,
      });
      console.log('Push subscription created, endpoint:', subscription.endpoint.substring(0, 50) + '...');
    } catch (error: any) {
      const errorMsg = `Failed to create push subscription: ${error.message || error}. This might be due to invalid VAPID keys or browser compatibility issues.`;
      console.error(errorMsg, error);
      throw new Error(errorMsg);
    }

    // Convert subscription to object
    const p256dhKey = subscription.getKey('p256dh');
    const authKey = subscription.getKey('auth');
    
    if (!p256dhKey || !authKey) {
      const error = 'Failed to get subscription keys';
      console.error(error);
      throw new Error(error);
    }

    const subscriptionData: PushSubscriptionData = {
      endpoint: subscription.endpoint,
      keys: {
        p256dh: arrayBufferToBase64(p256dhKey),
        auth: arrayBufferToBase64(authKey),
      },
    };

    // Send subscription to server
    let response: Response;
    try {
      // Use the same API URL configuration as the rest of the app
      const API_URL = import.meta.env.VITE_API_URL || '';
      const API_PREFIX = '/api';
      const baseURL = API_URL ? `${API_URL}${API_PREFIX}` : API_PREFIX;
      
      response = await fetch(`${baseURL}/push/subscribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(subscriptionData),
      });
    } catch (error: any) {
      const errorMsg = `Network error sending subscription: ${error.message || error}`;
      console.error(errorMsg);
      throw new Error(errorMsg);
    }

    if (!response.ok) {
      const errorText = await response.text();
      let errorDetail;
      try {
        const errorJson = JSON.parse(errorText);
        errorDetail = errorJson.detail || errorJson.message || errorText;
      } catch {
        errorDetail = errorText || `HTTP ${response.status}`;
      }
      const errorMsg = `Server error: ${errorDetail}`;
      console.error(errorMsg);
      throw new Error(errorMsg);
    }

    console.log('Subscribed to push notifications successfully');
    return subscriptionData;
  } catch (error: any) {
    console.error('Error subscribing to push notifications:', error);
    // Re-throw with more context for the UI
    throw error;
  }
}

/**
 * Unsubscribe from push notifications
 */
export async function unsubscribeFromPushNotifications(): Promise<boolean> {
  try {
    if (!('serviceWorker' in navigator)) {
      return false;
    }

    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();

    if (subscription) {
      await subscription.unsubscribe();

      // Notify server
      try {
        await fetch('/api/push/unsubscribe', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            endpoint: subscription.endpoint,
          }),
        });
      } catch (error) {
        console.error('Error notifying server of unsubscribe:', error);
      }

      console.log('Unsubscribed from push notifications');
      return true;
    }
    return false;
  } catch (error) {
    console.error('Error unsubscribing from push notifications:', error);
    return false;
  }
}

/**
 * Check if user is subscribed to push notifications
 */
export async function isSubscribedToPushNotifications(): Promise<boolean> {
  try {
    if (!('serviceWorker' in navigator)) {
      return false;
    }

    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    return !!subscription;
  } catch (error) {
    console.error('Error checking subscription status:', error);
    return false;
  }
}

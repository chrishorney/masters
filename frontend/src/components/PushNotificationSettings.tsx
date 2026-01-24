/**
 * Push Notification Settings Component
 * Allows users to subscribe/unsubscribe from push notifications
 */
import { useState, useEffect } from 'react';
import {
  subscribeToPushNotifications,
  unsubscribeFromPushNotifications,
  isSubscribedToPushNotifications,
} from '../utils/pushNotifications';

export function PushNotificationSettings() {
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [permission, setPermission] = useState<NotificationPermission>('default');
  const [isSupported, setIsSupported] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkSupportAndStatus();
  }, []);

  const checkSupportAndStatus = async () => {
    // Check if push notifications are supported
    const supported = 'Notification' in window && 'serviceWorker' in navigator && 'PushManager' in window;
    setIsSupported(supported);

    if (supported) {
      setPermission(Notification.permission);
      const subscribed = await isSubscribedToPushNotifications();
      setIsSubscribed(subscribed);
    }
  };

  const handleSubscribe = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const subscription = await subscribeToPushNotifications();
      if (subscription) {
        setIsSubscribed(true);
        setPermission(Notification.permission);
      } else {
        setError('Failed to subscribe. Please check your browser settings.');
      }
    } catch (error: any) {
      console.error('Error subscribing:', error);
      setError(error.message || 'Failed to subscribe to push notifications');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUnsubscribe = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const success = await unsubscribeFromPushNotifications();
      if (success) {
        setIsSubscribed(false);
      } else {
        setError('Failed to unsubscribe');
      }
    } catch (error: any) {
      console.error('Error unsubscribing:', error);
      setError(error.message || 'Failed to unsubscribe from push notifications');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isSupported) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4 md:p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Push Notifications
        </h3>
        <p className="text-sm text-gray-600">
          Push notifications are not supported in this browser.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4 md:p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Push Notifications
      </h3>
      
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {permission === 'denied' && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            Notifications are blocked. Please enable them in your browser settings.
          </p>
        </div>
      )}

      {isSubscribed ? (
        <div>
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-800 font-medium">
              ✓ You're subscribed to push notifications
            </p>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            You'll receive alerts for:
          </p>
          <ul className="text-sm text-gray-600 mb-4 list-disc list-inside space-y-1 ml-2">
            <li>Hole-in-ones</li>
            <li>Eagles and double eagles</li>
            <li>New leader announcements</li>
            <li>Big position changes</li>
            <li>Round completions</li>
          </ul>
          <button
            onClick={handleUnsubscribe}
            disabled={isLoading}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
          >
            {isLoading ? 'Unsubscribing...' : 'Unsubscribe'}
          </button>
        </div>
      ) : (
        <div>
          <p className="text-sm text-gray-600 mb-4">
            Get real-time notifications for exciting tournament events! You'll be alerted when:
          </p>
          <ul className="text-sm text-gray-600 mb-4 list-disc list-inside space-y-1 ml-2">
            <li>Players get hole-in-ones, eagles, or double eagles</li>
            <li>A new leader emerges</li>
            <li>Entries make big position moves</li>
            <li>Rounds complete</li>
          </ul>
          <button
            onClick={handleSubscribe}
            disabled={isLoading || permission === 'denied'}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
          >
            {isLoading ? 'Subscribing...' : 'Enable Notifications'}
          </button>
          {permission === 'denied' && (
            <p className="text-xs text-gray-500 mt-2">
              Please enable notifications in your browser settings to subscribe.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Time formatting utilities - all times displayed in Central Time
 */

/**
 * Format a date/time string to Central Time
 * @param dateString ISO date string or Date object
 * @param options Intl.DateTimeFormatOptions
 * @returns Formatted time string in Central Time
 */
export function formatCentralTime(
  dateString: string | Date,
  options: Intl.DateTimeFormatOptions = {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
    timeZone: 'America/Chicago'
  }
): string {
  let date: Date
  if (typeof dateString === 'string') {
    // If the string doesn't have timezone info, assume it's UTC
    // This handles timezone-naive ISO strings from the backend
    if (!dateString.includes('Z') && !dateString.includes('+') && !dateString.includes('-', 10)) {
      // No timezone indicator - assume UTC and append 'Z'
      date = new Date(dateString + 'Z')
    } else {
      date = new Date(dateString)
    }
  } else {
    date = dateString
  }
  return date.toLocaleString('en-US', {
    ...options,
    timeZone: 'America/Chicago'
  })
}

/**
 * Format a date/time string to Central Time with full date and time
 * @param dateString ISO date string or Date object
 * @returns Formatted time string (e.g., "Jan 23, 2026, 7:45 PM CT")
 */
export function formatCentralTimeFull(dateString: string | Date): string {
  return formatCentralTime(dateString, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
    timeZone: 'America/Chicago',
    timeZoneName: 'short'
  })
}

/**
 * Format a date/time string to Central Time (short format)
 * @param dateString ISO date string or Date object
 * @returns Formatted time string (e.g., "Jan 23, 7:45 PM")
 */
export function formatCentralTimeShort(dateString: string | Date): string {
  return formatCentralTime(dateString, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
    timeZone: 'America/Chicago'
  })
}

/**
 * Format a date to Central Time (date only)
 * @param dateString ISO date string or Date object
 * @returns Formatted date string (e.g., "Jan 23, 2026")
 */
export function formatCentralDate(dateString: string | Date): string {
  return formatCentralTime(dateString, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'America/Chicago'
  })
}

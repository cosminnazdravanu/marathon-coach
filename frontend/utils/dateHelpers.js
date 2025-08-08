export function getDateStringForDayNumber(dayNumber) {
  const today = new Date();

  // Get the day of the week (0 = Sunday, 1 = Monday, ..., 6 = Saturday)
  const currentDay = today.getDay();

  // Calculate how many days to subtract to get Monday
  const offset = currentDay === 0 ? 6 : currentDay - 1;

  const monday = new Date(today);
  monday.setDate(today.getDate() - offset);

  const date = new Date(monday);
  date.setDate(monday.getDate() + (dayNumber - 1));

  return date.toISOString().slice(0, 10); // Format YYYY-MM-DD
}

export function getLabelForDayNumber(dayNumber) {
  const dateStr = getDateStringForDayNumber(dayNumber);
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-GB", {
    weekday: "short",
    day: "2-digit",
    month: "short"
  }); // e.g., "Mon, 29 Jul"
}

export function getLabelForDate(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-GB", {
    weekday: "short",
    day:      "2-digit",
    month:    "short"
  });
}

/**
 * generateInitialDates
 * Generates an array of consecutive dates spanning a given number of weeks before
 * and after the current week (Monday-based), normalized to local time.
 * Time-zone: operates on local Date objects (midnight local); adjust externally if UTC
 * param {number} weeksBack Number of weeks before current week to include
 * param {number} weeksForward Number of weeks after current week to include
 * returns {Date[]} Array of Date objects starting Monday of (currentWeek - weeksBack)
 */
export function generateInitialDates(weeksBack, weeksForward) {
  const now = new Date();
  // Determine offset so Monday is day 0
  const mondayOffset = (now.getDay() + 6) % 7;
  // Compute this week’s Monday
  const monday = new Date(now);
  monday.setDate(now.getDate() - mondayOffset);
  // Back up by weeksBack weeks
  const start = new Date(monday);
  start.setDate(monday.getDate() - weeksBack * 7);

  const totalWeeks = weeksBack + weeksForward + 1;
  const totalDays = totalWeeks * 7;
  return Array.from({ length: totalDays }, (_, i) => {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    return d;
  });
}

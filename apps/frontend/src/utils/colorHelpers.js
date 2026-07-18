/**
 * Maps a zone density state to a CSS class name.
 * 
 * @param {string} state - The color state (green, yellow, red, critical)
 * @returns {string} The matching CSS class name.
 */
export function colorClass(state) {
  const map = {
    green: 'zone-green',
    yellow: 'zone-yellow',
    red: 'zone-red',
    critical: 'zone-critical'
  };
  return map[state] || 'zone-green';
}

/**
 * Maps a zone density state to a user-friendly accessible text label.
 * 
 * @param {string} state - The color state (green, yellow, red, critical)
 * @returns {string} The text label.
 */
export function colorLabel(state) {
  const map = {
    green: 'Low',
    yellow: 'Moderate',
    red: 'High',
    critical: 'Critical'
  };
  return map[state] || state;
}

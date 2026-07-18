/**
 * Application constants for the ArenaIQ frontend.
 */

/**
 * Time threshold in milliseconds before telemetry data is considered stale.
 * @type {number}
 */
export const STALE_THRESHOLD = 5000;

/**
 * Default WebSocket reconnect delay in milliseconds.
 * @type {number}
 */
export const WS_RECONNECT_DELAY = 3000;

/**
 * Standard colors for the different crowd density states.
 * @type {Object.<string, string>}
 */
export const STATE_COLORS = {
  green: '#22c55e',
  yellow: '#eab308',
  red: '#ef4444',
  critical: '#a855f7',
};

/**
 * Human-readable labels for the different crowd density states.
 * @type {Object.<string, string>}
 */
export const STATE_LABELS = {
  green: 'Low',
  yellow: 'Moderate',
  red: 'High',
  critical: 'Critical',
};

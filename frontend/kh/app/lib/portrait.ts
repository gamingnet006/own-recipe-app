// KH: phones stay upright (D71). iOS ignores the manifest orientation and has no screen.orientation.lock, so a
// cover tells the person to turn the phone back; iPads and computers never get it.

/** Short side below this (CSS px of the screen, not the window) is a phone; the smallest iPad has 744. */
export const PHONE_MAX_SHORT_SIDE = 500;

/** Whether the screen is a phone held sideways: a touch device with a short screen side under 500 px. The screen,
 * not the window, is measured, so a narrow split view on an iPad never counts. */
export function isPhoneLandscape(screen: { width: number; height: number }, pointerCoarse: boolean, landscape: boolean): boolean {
  return landscape && pointerCoarse && Math.min(screen.width, screen.height) < PHONE_MAX_SHORT_SIDE;
}

/** Whether the device is a phone at all, for locking the orientation of an installed Android app. */
export function isPhone(screen: { width: number; height: number }, pointerCoarse: boolean): boolean {
  return isPhoneLandscape(screen, pointerCoarse, true);
}

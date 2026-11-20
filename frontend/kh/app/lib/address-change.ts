// KH: the card "Neue Adresse" (D85): shown once per person and device after Kochheft moved to another address, because
// shortcuts and home-screen icons still point to the old one. The change's time (from /api/kh/features) is the key.

/** The storage key of what this person has seen on this device. */
export const addressSeenKey = (userId: string) => `kh-address-seen:${userId}`;

/** True while a change is on record (CHANGED_AT) that differs from the one already seen (SEEN, null: none). */
export function addressCardDue(changedAt: string | null, seen: string | null): boolean {
  return !!changedAt && changedAt !== seen;
}

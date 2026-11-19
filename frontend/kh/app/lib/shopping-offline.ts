// KH: the shopping page without network (D63): the queue of changes made while offline and how it is replayed, and what
// the page keeps of the last loaded lists on the device (localStorage, per user) to show it at once.

/** The fields of a list item a change sets (the ones the detail sheet and the tiles edit). */
export type Fields = Record<string, unknown>;

/**
 * A change made while offline; the add carries a TEMP-ID, the id its local stand-in item has until the server knows it,
 * and the food by id, or by NAME and LABEL-ID (department) when the group has no such food yet.
 */
export type QueuedOp
  = | { kind: "change"; itemId: string; changes: Fields }
    | { kind: "add"; tempId: string; listId: string; foodId: string | null; name: string; labelId: string | null; fields: Fields }
    | { kind: "remove"; itemId: string };

/** What sending one queued change came to: sent, the item or list is gone meanwhile, no answer at all, or refused. */
export type Outcome = "done" | "gone" | "offline" | "failed";

const LOCAL_PREFIX = "local-";
const KEY_PREFIX = "kh-shop-offline:";

let counter = 0;

/** A fresh id for an item that only exists on this device yet. */
export const newLocalId = (): string => `${LOCAL_PREFIX}${Date.now().toString(36)}-${(counter++).toString(36)}`;

export const isLocalId = (id: string): boolean => id.startsWith(LOCAL_PREFIX);

/** Whether a failed request got no answer at all (no network), as opposed to an answer with an error status. */
export const noAnswer = (error: unknown): boolean => !!error && !(error as { response?: unknown }).response;

/**
 * QUEUE with OP added. A change of an item that is still to be added goes into that add, and a second change of the
 * same item into its first, so the queue stays short; a removal drops what was queued for the item (and is dropped
 * itself when the item's add was still in the queue; a local item whose add is on its way needs the removal).
 */
export function enqueue(queue: QueuedOp[], op: QueuedOp): QueuedOp[] {
  if (op.kind === "add") return [...queue, op];
  if (op.kind === "remove") {
    const rest = queue.filter(entry => (entry.kind === "add" ? entry.tempId : entry.itemId) !== op.itemId);
    const addWasQueued = queue.some(entry => entry.kind === "add" && entry.tempId === op.itemId);
    return addWasQueued ? rest : [...rest, op];
  }
  const index = queue.findIndex(entry => (entry.kind === "add" ? entry.tempId : entry.kind === "change" ? entry.itemId : "") === op.itemId);
  const target = queue[index];
  if (!target || target.kind === "remove") return [...queue, op];
  const merged = target.kind === "add"
    ? { ...target, fields: { ...target.fields, ...op.changes } }
    : { ...target, changes: { ...target.changes, ...op.changes } };
  return queue.map((entry, at) => (at === index ? merged : entry));
}

/**
 * Sends the queued changes one after the other with RUN, oldest first. An op leaves the queue while it is sent (changes
 * made meanwhile become ops of their own); it goes back to the front and the replay stops when there is no network;
 * a vanished item is skipped. Returns how many were refused by the server and dropped.
 */
export async function replay(
  store: { get: () => QueuedOp[]; set: (queue: QueuedOp[]) => void },
  run: (op: QueuedOp) => Promise<Outcome>,
): Promise<number> {
  let failed = 0;
  for (let op = store.get()[0]; op; op = store.get()[0]) {
    store.set(store.get().slice(1));
    const outcome = await run(op);
    if (outcome === "offline") {
      store.set([op, ...store.get()]);
      break;
    }
    if (outcome === "failed") failed++;
  }
  return failed;
}

/** The value kept under NAME for the user; FALLBACK when there is none or the storage is blocked or broken. */
export function readStored<T>(userId: string, name: string, fallback: T): T {
  try {
    const text = localStorage.getItem(`${KEY_PREFIX}${userId}:${name}`);
    return text ? (JSON.parse(text) as T) : fallback;
  }
  catch {
    return fallback;
  }
}

/** Keeps VALUE under NAME for the user; a full or blocked storage only means the next start has less to show. */
export function writeStored(userId: string, name: string, value: unknown): void {
  try {
    localStorage.setItem(`${KEY_PREFIX}${userId}:${name}`, JSON.stringify(value));
  }
  catch (error) {
    console.warn("Could not keep the shopping list for offline use:", error);
  }
}

const LAST_USER = "last-user";

/** Remembers who was signed in, so that a start without network (no session answer) still finds the stored lists. */
export function rememberUser(userId: string): void {
  try {
    localStorage.setItem(`${KEY_PREFIX}${LAST_USER}`, userId);
  }
  catch {
    // only the start without network misses it
  }
}

/** The user remembered by rememberUser; "" when none. */
export function lastUser(): string {
  try {
    return localStorage.getItem(`${KEY_PREFIX}${LAST_USER}`) ?? "";
  }
  catch {
    return "";
  }
}

/** Forgets everything kept for offline use, of every user: at sign-out and when the offline add-on goes off. */
export function clearStored(): void {
  try {
    Object.keys(localStorage).filter(key => key.startsWith(KEY_PREFIX)).forEach(key => localStorage.removeItem(key));
  }
  catch {
    // nothing was kept where the storage is blocked
  }
}

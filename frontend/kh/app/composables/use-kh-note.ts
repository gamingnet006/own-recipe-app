// KH: the household's note on a recipe (D82) as one shared state, so the recipe page and cook mode show the same text
// and a save in one is seen in the other at once.
import { KhNotesApi } from "../lib/api/notes";
import { useRequests } from "~/composables/api/api-client";
import { useGlobalI18n } from "~/composables/use-global-i18n";
import { alert } from "~/composables/use-toast";

// "user id:recipe id" -> the note's text; "" when the recipe has none; no entry while it is not loaded (or failed to
// load). The user id is part of the key, so a switch to another account never shows the first one's notes.
const notes = reactive(new Map<string, string>());

/** Forgets every note, for a sign-out (the next person on a shared device starts empty). */
export function resetKhNotes(): void {
  notes.clear();
}

/** The note of the recipe with ID: its text (undefined until loaded), and a save that tells the person about a failure
 * and leaves the old text. Call it while a component is set up. */
export function useKhNote(id: () => string) {
  const api = new KhNotesApi(useRequests());
  const auth = useMealieAuth();
  const keyOf = () => `${auth.user.value?.id ?? ""}:${id()}`;

  /** Loads the note once per recipe and session. */
  async function load() {
    const recipeId = id();
    const key = keyOf();
    if (!recipeId || notes.has(key)) return;
    const { data, error } = await api.get(recipeId);
    if (!error) notes.set(key, data?.text ?? "");
  }

  /** Stores TEXT as the note (empty deletes it); false when the server refused. */
  async function save(text: string): Promise<boolean> {
    const key = keyOf();
    const { error } = await api.put(id(), text);
    if (error) {
      alert.error(useGlobalI18n().t("events.something-went-wrong"));
      return false;
    }
    notes.set(key, text.trim());
    return true;
  }

  return { text: computed(() => notes.get(keyOf())), load, save };
}

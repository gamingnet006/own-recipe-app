// KH: tests for the shared note state (D82): loaded once per person and recipe, a save is shown at once, a failed save
// keeps the old text, and nothing of one person's notes is visible to the next one (sign-out, account switch).
import { beforeEach, describe, expect, test, vi } from "vitest";
import { ref } from "vue";
import { resetKhNotes, useKhNote } from "../composables/use-kh-note";

const get = vi.hoisted(() => vi.fn());
const put = vi.hoisted(() => vi.fn());
const error = vi.hoisted(() => vi.fn());
const userId = vi.hoisted(() => ({ value: "u1" as string | undefined }));

vi.mock("../lib/api/notes", () => ({ KhNotesApi: class { get = get; put = put; } }));
vi.mock("~/composables/api/api-client", () => ({ useRequests: () => ({}) }));
vi.mock("~/composables/use-global-i18n", () => ({ useGlobalI18n: () => ({ t: (key: string) => key }) }));
vi.mock("~/composables/use-toast", () => ({ alert: { error } }));
vi.stubGlobal("reactive", <T extends object>(value: T) => value);
vi.stubGlobal("computed", (fn: () => unknown) => ({ get value() { return fn(); } }));
vi.stubGlobal("useMealieAuth", () => ({ user: ref(userId.value ? { id: userId.value } : null) }));

beforeEach(() => {
  get.mockReset();
  put.mockReset();
  error.mockReset();
  userId.value = "u1";
  resetKhNotes();
});

describe("useKhNote", () => {
  test("loads once per recipe", async () => {
    get.mockResolvedValue({ data: { text: "Weniger Zucker" }, error: null });
    const note = useKhNote(() => "r1");
    await note.load();
    await note.load();
    expect(get).toHaveBeenCalledTimes(1);
    expect(note.text.value).toBe("Weniger Zucker");
  });

  test("a recipe without a note is an empty text; a failed load leaves it unknown", async () => {
    get.mockResolvedValue({ data: null, error: null });
    const none = useKhNote(() => "r1");
    await none.load();
    expect(none.text.value).toBe("");
    get.mockResolvedValue({ data: null, error: "boom" });
    const failed = useKhNote(() => "r2");
    await failed.load();
    expect(failed.text.value).toBeUndefined();
  });

  test("a save shows the trimmed text; a failed save keeps the old one and tells the person", async () => {
    get.mockResolvedValue({ data: { text: "alt" }, error: null });
    const note = useKhNote(() => "r1");
    await note.load();
    put.mockResolvedValue({ data: { text: "neu" }, error: null });
    expect(await note.save("  neu ")).toBe(true);
    expect(note.text.value).toBe("neu");
    put.mockResolvedValue({ data: null, error: "boom" });
    expect(await note.save("kaputt")).toBe(false);
    expect(note.text.value).toBe("neu");
    expect(error).toHaveBeenCalled();
  });

  test("the next person never sees the previous person's note", async () => {
    get.mockResolvedValue({ data: { text: "Notiz von u1" }, error: null });
    await useKhNote(() => "r1").load();
    userId.value = "u2"; // another account switched to without a reload
    expect(useKhNote(() => "r1").text.value).toBeUndefined();
    userId.value = "u1";
    resetKhNotes(); // sign-out
    expect(useKhNote(() => "r1").text.value).toBeUndefined();
  });
});

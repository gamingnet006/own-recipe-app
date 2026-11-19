// KH: tests for sharing the shopping list (D56): nothing to share gives a hint, a cancelled share sheet is silent, any
// other failure and a missing share sheet copy instead.
import { beforeEach, describe, expect, test, vi } from "vitest";
import { useKhShareList } from "../composables/use-kh-share-list";

const copy = vi.hoisted(() => vi.fn());
const copied = vi.hoisted(() => ({ value: true }));
const toast = vi.hoisted(() => ({ info: vi.fn(), success: vi.fn(), error: vi.fn() }));
const share = vi.hoisted(() => vi.fn());

vi.mock("@vueuse/core", () => ({ useClipboard: () => ({ copy, copied, isSupported: { value: true } }) }));
vi.mock("~/composables/use-toast", () => ({ alert: toast }));
vi.mock("vue-i18n", () => ({ useI18n: () => ({ t: (key: string) => key }) }));

const items = [{ display: "2 eggs", checked: false }, { display: "milk", checked: true }];

beforeEach(() => {
  vi.clearAllMocks();
  share.mockReset();
  copied.value = true;
  vi.stubGlobal("navigator", { share });
});

describe("shareList", () => {
  test("hands the open items to the share sheet", async () => {
    await useKhShareList().shareList("Einkauf", items);
    expect(share).toHaveBeenCalledWith({ title: "Einkauf", text: "2 eggs" });
    expect(copy).not.toHaveBeenCalled();
  });

  test("a list with nothing open is neither shared nor copied", async () => {
    await useKhShareList().shareList("Einkauf", [{ display: "milk", checked: true }]);
    expect(toast.info).toHaveBeenCalledWith("kh.share.empty");
    expect(share).not.toHaveBeenCalled();
    expect(copy).not.toHaveBeenCalled();
  });

  test("a cancelled share sheet shows nothing", async () => {
    share.mockRejectedValue(new DOMException("cancelled", "AbortError"));
    await useKhShareList().shareList("Einkauf", items);
    expect(copy).not.toHaveBeenCalled();
    expect(toast.error).not.toHaveBeenCalled();
  });

  test("any other failure copies the text instead", async () => {
    share.mockRejectedValue(new DOMException("not allowed", "NotAllowedError"));
    await useKhShareList().shareList("Einkauf", items);
    expect(copy).toHaveBeenCalledWith("2 eggs");
    expect(toast.success).toHaveBeenCalledWith("kh.share.copied");
  });

  test("without a share sheet it copies", async () => {
    vi.stubGlobal("navigator", {});
    await useKhShareList().shareList("Einkauf", items);
    expect(copy).toHaveBeenCalledWith("2 eggs");
  });
});

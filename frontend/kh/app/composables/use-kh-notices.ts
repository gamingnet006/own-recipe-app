// KH: the bell (D39): a notice in the reader's words, which notices are new since the last check, and the bell's
// state, checked now, every few minutes and whenever the app comes back to the front.
import { useRequests } from "~/composables/api/api-client";
import { alert } from "~/composables/use-toast";
import { KhNoticesApi, type KhNotice } from "../lib/api/notices";
import { clockTime } from "./use-kh-ai";

type Translate = (key: string, values?: Record<string, string>) => string;

/** The notice in words, e.g. "Gemini: Kontingent aufgebraucht bis 9:00. Ich nehme jetzt Groq." */
export function noticeText(notice: KhNotice, t: Translate, time: (d: Date) => string): string {
  const values = {
    provider: notice.provider ?? "",
    until: notice.until ? time(new Date(notice.until)) : "",
    next: notice.nextProvider ?? "",
  };
  const text = t(`kh.notices.${notice.kind}`, values);
  return notice.nextProvider ? text + t("kh.notices.next", values) : text;
}

/** The notices whose id was not seen before, for the short hint at the bottom. */
export function freshNotices(items: KhNotice[], known: Set<string>): KhNotice[] {
  return items.filter(notice => !known.has(notice.id));
}

/** FN, but a call while one is still running is dropped: opening the app also reports it visible. */
export function oneAtATime(fn: () => Promise<void>): () => Promise<void> {
  let running = false;
  return async () => {
    if (running) return;
    running = true;
    try {
      await fn();
    }
    finally {
      running = false;
    }
  };
}

/** The bell's notices and unread count. Notices that arrive while the app is open show once at the bottom; those
 * from before it opened only count in the badge. */
export function useKhNotices() {
  const api = new KhNoticesApi(useRequests());
  const i18n = useI18n();
  const { $khFeatures } = useNuxtApp();
  const items = ref<KhNotice[]>([]);
  const unread = ref(0);
  const known = new Set<string>();
  let loaded = false;
  let timer: ReturnType<typeof setInterval> | undefined;

  const load = oneAtATime(async () => {
    const { data } = await api.list();
    if (!data) return;
    const fresh = loaded ? freshNotices(data.items, known) : [];
    data.items.forEach(notice => known.add(notice.id));
    loaded = true;
    items.value = data.items;
    unread.value = data.unread;
    const time = (d: Date) => clockTime(d, i18n.locale.value);
    fresh.forEach(notice => alert.info(noticeText(notice, (key, values) => i18n.t(key, values ?? {}), time)));
  });

  async function open() {
    await api.read();
    unread.value = 0;
  }

  function onVisible() {
    if (document.visibilityState === "visible") load();
  }

  onMounted(() => {
    load();
    timer = setInterval(load, $khFeatures.noticePollMinutes * 60_000);
    document.addEventListener("visibilitychange", onVisible);
  });
  onBeforeUnmount(() => {
    clearInterval(timer);
    document.removeEventListener("visibilitychange", onVisible);
  });

  return { items, unread, open };
}

// KH: keeps phones upright (D71): a cover with "Bitte dreh dein Handy hochkant." while a phone is held sideways, and
// on an installed Android app a try to lock the orientation. Plain DOM, so it covers every layout, also cook mode.
import { isPhone, isPhoneLandscape } from "../lib/portrait";

const SVG = "http://www.w3.org/2000/svg";

/** A phone outline as an SVG, built node by node (no HTML parsing). */
function phoneIcon(): SVGElement {
  const svg = document.createElementNS(SVG, "svg");
  const attrs = { "viewBox": "0 0 24 24", "width": "72", "height": "72", "fill": "none", "stroke": "currentColor", "stroke-width": "1.5", "stroke-linecap": "round", "aria-hidden": "true" };
  Object.entries(attrs).forEach(([name, value]) => svg.setAttribute(name, value));
  const body = document.createElementNS(SVG, "rect");
  Object.entries({ x: "7", y: "2", width: "10", height: "20", rx: "2" }).forEach(([name, value]) => body.setAttribute(name, value));
  const button = document.createElementNS(SVG, "path");
  button.setAttribute("d", "M11 18.5h2");
  svg.append(body, button);
  return svg;
}
const STYLE = `
.kh-portrait{position:fixed;inset:0;z-index:100000;display:none;flex-direction:column;align-items:center;justify-content:center;gap:16px;
background:#fff;color:#222;font:500 18px/1.4 system-ui,sans-serif;text-align:center;padding:24px}
.kh-portrait.kh-on{display:flex}
.kh-portrait svg{animation:kh-turn 2.4s ease-in-out infinite}
@keyframes kh-turn{0%,30%{transform:rotate(90deg)}70%,100%{transform:rotate(0)}}
@media (prefers-reduced-motion:reduce){.kh-portrait svg{animation:none}}
@media (prefers-color-scheme:dark){.kh-portrait{background:#111;color:#eee}}`;

export default defineNuxtPlugin((nuxtApp) => {
  const landscape = window.matchMedia("(orientation: landscape)");
  const coarse = window.matchMedia("(pointer: coarse)");

  const cover = document.createElement("div");
  cover.className = "kh-portrait";
  cover.setAttribute("role", "alert");
  const message = document.createElement("div");
  message.textContent = (nuxtApp.$i18n as { t: (key: string) => string }).t("kh.portrait.message");
  cover.append(phoneIcon(), message);
  const style = document.createElement("style");
  style.textContent = STYLE;
  document.head.append(style);
  document.body.append(cover);

  const update = () => cover.classList.toggle("kh-on", isPhoneLandscape(screen, coarse.matches, landscape.matches));
  landscape.addEventListener("change", update);
  update();

  // Android only: iOS has no lock, so the cover above does that job there; a refusal is fine, the cover still works
  const standalone = window.matchMedia("(display-mode: standalone)").matches;
  if (standalone && isPhone(screen, coarse.matches)) {
    void (screen.orientation as { lock?: (o: string) => Promise<void> }).lock?.("portrait").catch(() => undefined);
  }
});

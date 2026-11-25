// KH: the lines the wizard's summary adds for Kochheft's own choices (D83): language, colour, the add-ons preset, the
// people created, AI.
import { currentPreset } from "../lib/addons";
import { presetLabelKey } from "../lib/setup-wizard";
import { KH_LOCALES } from "../lib/locale";
import { khInstallationAccent } from "./use-kh-accent";
import { khAddons } from "./use-kh-addons";
import { khFamily } from "./use-kh-setup-family";

/** AIPROVIDERS is how many AI providers the group has right now (they are saved as soon as they are made). */
export function useKhSetupSummary(aiProviders: Ref<number>) {
  const i18n = useI18n();
  return computed(() => [
    { text: i18n.t("kh.wizard.summary.language"), value: KH_LOCALES.find(language => language.value === i18n.locale.value)?.name ?? i18n.locale.value },
    { text: i18n.t("kh.wizard.summary.accent"), value: i18n.t(`kh.accent.${khInstallationAccent.value ?? "salbei"}`) },
    { text: i18n.t("kh.wizard.summary.addons"), value: i18n.t(presetLabelKey(currentPreset(khAddons.flags))) },
    {
      text: i18n.t("kh.wizard.summary.family"),
      value: khFamily.created.length ? khFamily.created.map(person => person.name).join(", ") : i18n.t("kh.wizard.summary.nobody"),
    },
    { text: i18n.t("kh.wizard.summary.ai"), value: aiProviders.value ? i18n.t("general.yes") : i18n.t("general.no") },
  ].map(line => ({ display: true, ...line })));
}

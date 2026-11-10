// KH: where free AI keys come from (D39), shown under the AI providers. Checked on the providers' own pages on the
// date below; free tiers change often, so the date shows with the list.

/** The day the list was checked. */
export const FREE_AI_KEYS_DATE = "2026-11-04";

export interface FreeAiKey {
  name: string;
  keyUrl: string; // where the key is made
  baseUrl: string; // what goes into the provider's address field
  note: { de: string; en: string };
}

export const FREE_AI_KEYS: FreeAiKey[] = [
  {
    name: "Google AI Studio (Gemini)",
    keyUrl: "https://aistudio.google.com/apikey",
    baseUrl: "https://generativelanguage.googleapis.com/v1beta/openai/",
    note: {
      de: "Liest Fotos; im Gratis-Angebot darf Google die Daten zur Verbesserung nutzen.",
      en: "Reads photos; on the free tier Google may use the data to improve its products.",
    },
  },
  {
    name: "Groq",
    keyUrl: "https://console.groq.com/keys",
    baseUrl: "https://api.groq.com/openai/v1",
    note: {
      de: "Sehr schnell; die feste Antwortform können nur neuere Modelle.",
      en: "Very fast; only newer models give the fixed answer form.",
    },
  },
  {
    name: "Mistral",
    keyUrl: "https://console.mistral.ai/api-keys",
    baseUrl: "https://api.mistral.ai/v1",
    note: {
      de: "Kostenloser „Free mode“; die Datenschutz-Einstellungen in der Konsole ansehen.",
      en: "Free \"Free mode\"; look at the privacy settings in the console.",
    },
  },
  {
    name: "OpenRouter",
    keyUrl: "https://openrouter.ai/settings/keys",
    baseUrl: "https://openrouter.ai/api/v1",
    note: {
      de: "Nur Modelle, deren Name auf „:free“ endet; 50 Anfragen am Tag.",
      en: "Only models whose name ends in \":free\"; 50 requests a day.",
    },
  },
  {
    name: "SambaNova",
    keyUrl: "https://cloud.sambanova.ai",
    baseUrl: "https://api.sambanova.ai/v1",
    note: {
      de: "Ohne Zahlungsmittel 20 Anfragen am Tag je Modell.",
      en: "Without a payment method 20 requests a day per model.",
    },
  },
  {
    name: "Cloudflare Workers AI",
    keyUrl: "https://dash.cloudflare.com/profile/api-tokens",
    baseUrl: "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/ai/v1",
    note: {
      de: "API-Token mit „Workers AI“; statt <ACCOUNT_ID> kommt die Konto-ID in die Adresse; 10.000 „Neurons“ am Tag.",
      en: "API token with \"Workers AI\"; the account ID replaces <ACCOUNT_ID> in the address; 10,000 \"neurons\" a day.",
    },
  },
  {
    name: "Z.ai (GLM)",
    keyUrl: "https://z.ai/manage-apikey/apikey-list",
    baseUrl: "https://api.z.ai/api/paas/v4/",
    note: {
      de: "Die Flash-Modelle sind kostenlos, GLM-4.6V-Flash liest auch Fotos; Firma in Singapur, die Daten werden dort verarbeitet.",
      en: "The Flash models are free, GLM-4.6V-Flash also reads photos; a company in Singapore, the data is processed there.",
    },
  },
  {
    name: "Vercel AI Gateway",
    keyUrl: "https://vercel.com/d?to=%2F%5Bteam%5D%2F%7E%2Fai-gateway&title=Go+to+AI+Gateway",
    baseUrl: "https://ai-gateway.vercel.sh/v1",
    note: {
      de: "Monatliches Gratis-Guthaben für ausgewählte Modelle; wer Guthaben kauft, bekommt es nicht mehr.",
      en: "Monthly free credit for selected models; buying credits ends it.",
    },
  },
  {
    name: "Cohere",
    keyUrl: "https://dashboard.cohere.com/api-keys",
    baseUrl: "https://api.cohere.ai/compatibility/v1",
    note: {
      de: "Test-Schlüssel mit 1.000 Anfragen im Monat und 20 pro Minute, zum Ausprobieren gedacht.",
      en: "Trial key with 1,000 requests a month and 20 a minute, meant for trying it out.",
    },
  },
  {
    name: "NVIDIA",
    keyUrl: "https://build.nvidia.com",
    baseUrl: "https://integrate.api.nvidia.com/v1",
    note: {
      de: "Einmalig 1.000 Credits zum Ausprobieren, bis 40 Anfragen pro Minute.",
      en: "1,000 one-time credits to try it out, up to 40 requests a minute.",
    },
  },
];

/** The places whose address one of the group's providers uses, by name; compared by address without case and last
 * slash, so a provider counts however the address was typed. Lets the list tick off what is already set up. */
export function setUpPlaces(baseUrls: (string | null)[]): Set<string> {
  const plain = (url: string) => url.trim().toLowerCase().replace(/\/+$/, "");
  const used = new Set(baseUrls.filter((url): url is string => !!url).map(plain));
  return new Set(FREE_AI_KEYS.filter(place => used.has(plain(place.baseUrl))).map(place => place.name));
}

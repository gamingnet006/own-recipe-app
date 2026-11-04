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
    name: "Cerebras",
    keyUrl: "https://cloud.cerebras.ai",
    baseUrl: "https://api.cerebras.ai/v1",
    note: {
      de: "Tageskontingent; die Bedingungen beim Anmelden prüfen.",
      en: "Daily quota; check the terms when signing up.",
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
    name: "NVIDIA",
    keyUrl: "https://build.nvidia.com",
    baseUrl: "https://integrate.api.nvidia.com/v1",
    note: {
      de: "Startguthaben für Entwickler, bis 40 Anfragen pro Minute.",
      en: "Starter credits for developers, up to 40 requests a minute.",
    },
  },
  {
    name: "Hugging Face",
    keyUrl: "https://huggingface.co/settings/tokens",
    baseUrl: "https://router.huggingface.co/v1",
    note: {
      de: "Kleines Guthaben jeden Monat.",
      en: "A small allowance every month.",
    },
  },
  {
    name: "Cloudflare Workers AI",
    keyUrl: "https://dash.cloudflare.com/profile/api-tokens",
    baseUrl: "https://api.cloudflare.com/client/v4/accounts/<Konto-ID>/ai/v1",
    note: {
      de: "API-Token mit „Workers AI“; die Konto-ID kommt in die Adresse; 10.000 „Neurons“ am Tag.",
      en: "API token with \"Workers AI\"; the account ID goes into the address; 10,000 \"neurons\" a day.",
    },
  },
  {
    name: "Cohere",
    keyUrl: "https://dashboard.cohere.com/api-keys",
    baseUrl: "https://api.cohere.ai/compatibility/v1",
    note: {
      de: "Test-Schlüssel mit etwa 1.000 Anfragen im Monat, nur für Privates.",
      en: "Trial key with about 1,000 requests a month, for private use only.",
    },
  },
];

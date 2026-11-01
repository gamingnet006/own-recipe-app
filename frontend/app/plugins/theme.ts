import { themeRequestUrl } from "~~/kh/app/lib/theme"; // KH: theme request per release (D38)

// KH: dark text on the light green of the dark theme, 6.7:1 instead of 2.7:1 with white (D38)
const KH_DARK_ON_PRIMARY = { "on-primary": "#0E1A13" };

export interface ThemeConfig {
  lightPrimary: string;
  lightAccent: string;
  lightSecondary: string;
  lightSuccess: string;
  lightInfo: string;
  lightWarning: string;
  lightError: string;
  darkPrimary: string;
  darkAccent: string;
  darkSecondary: string;
  darkSuccess: string;
  darkInfo: string;
  darkWarning: string;
  darkError: string;
}

let __cachedTheme: ThemeConfig | undefined;

async function fetchTheme(buildId: string): Promise<ThemeConfig | undefined> {
  const route = themeRequestUrl(buildId); // KH: a new release asks anew despite the week-long cache (D38)

  try {
    const response = await fetch(route);
    const data = await response.json();
    return data as ThemeConfig;
  }
  catch {
    return undefined;
  }
}

export default defineNuxtPlugin(async (nuxtApp) => {
  nuxtApp.hook("vuetify:before-create", async ({ vuetifyOptions }) => {
    let theme = __cachedTheme;
    if (!theme) {
      theme = await fetchTheme(nuxtApp.$config.app.buildId ?? ""); // KH: see fetchTheme
      __cachedTheme = theme;
    }
    vuetifyOptions.theme = {
      defaultTheme: nuxtApp.$config.public.useDark ? "dark" : "light",
      variations: {
        colors: ["primary", "accent", "secondary", "success", "info", "warning", "error", "background"],
        lighten: 3,
        darken: 3,
      },
      // KH: look "Salbei" as fallback too, and a light ground like the dark one below (D38)
      themes: {
        light: {
          dark: false,
          colors: {
            background: "#F4F5F1",
            primary: theme?.lightPrimary ?? "#2F7A55",
            accent: theme?.lightAccent ?? "#007A99",
            secondary: theme?.lightSecondary ?? "#973542",
            success: theme?.lightSuccess ?? "#43A047",
            info: theme?.lightInfo ?? "#1976d2",
            warning: theme?.lightWarning ?? "#FF6D00",
            error: theme?.lightError ?? "#EF5350",
          },
        },
        dark: {
          dark: true,
          colors: {
            primary: theme?.darkPrimary ?? "#4FB07E",
            ...KH_DARK_ON_PRIMARY,
            accent: theme?.darkAccent ?? "#007A99",
            secondary: theme?.darkSecondary ?? "#973542",
            success: theme?.darkSuccess ?? "#43A047",
            info: theme?.darkInfo ?? "#1976d2",
            warning: theme?.darkWarning ?? "#FF6D00",
            error: theme?.darkError ?? "#EF5350",
            background: "#1E1E1E",
            surface: "#1E1E1E",
          },
        },
      },
    };
  });
});

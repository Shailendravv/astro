import { defineRouting } from "next-intl/routing";

// UI languages for Release 1 (D-002). The default only decides where "/" redirects; it is not a
// calculation convention.
export const routing = defineRouting({
  locales: ["en", "hi"],
  defaultLocale: "en",
});

export type Locale = (typeof routing.locales)[number];

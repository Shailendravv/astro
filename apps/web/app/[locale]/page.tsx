import { hasLocale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import Link from "next/link";
import { notFound } from "next/navigation";

import { HealthStatus } from "@/components/HealthStatus";
import { routing } from "@/i18n/routing";

export default async function HomePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }
  setRequestLocale(locale);
  const t = await getTranslations("Home");

  return (
    <main>
      <h1>{t("title")}</h1>
      <p>{t("subtitle")}</p>

      <nav aria-label={t("language")}>
        <span>{t("language")}: </span>
        <Link href="/en" lang="en" aria-current={locale === "en" ? "page" : undefined}>
          {t("english")}
        </Link>
        {" | "}
        <Link href="/hi" lang="hi" aria-current={locale === "hi" ? "page" : undefined}>
          {t("hindi")}
        </Link>
      </nav>

      <HealthStatus apiBase={process.env.NEXT_PUBLIC_API_BASE ?? ""} />
    </main>
  );
}

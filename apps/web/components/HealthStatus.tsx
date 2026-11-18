"use client";

import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

type Checks = {
  database: string;
  ephemeris_files: string;
  library_mount: string;
};

type Health = {
  status: string;
  checks: Checks;
  ai_enabled: boolean;
};

type State =
  | { kind: "checking" }
  | { kind: "unreachable" }
  | { kind: "notConfigured" }
  | { kind: "loaded"; health: Health };

// Status is shown as a symbol plus a text label, never by colour alone (docs/ui-ux.md).
const SYMBOLS: Record<string, string> = {
  ok: "✓",
  enabled: "✓",
  disabled: "–",
  not_configured: "–",
  degraded: "!",
  error: "✗",
  unreachable: "✗",
};

const KNOWN_VALUES = new Set(Object.keys(SYMBOLS));

export function HealthStatus({ apiBase }: { apiBase: string }) {
  const t = useTranslations("Health");
  const [state, setState] = useState<State>(
    apiBase ? { kind: "checking" } : { kind: "notConfigured" },
  );

  useEffect(() => {
    if (!apiBase) return;
    const controller = new AbortController();
    // The API answers 503 with a JSON body when a dependency is down, so read the body either way.
    fetch(`${apiBase}/health`, { signal: controller.signal })
      .then((response) => response.json() as Promise<Health>)
      .then((health) => setState({ kind: "loaded", health }))
      .catch((error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          setState({ kind: "unreachable" });
        }
      });
    return () => controller.abort();
  }, [apiBase]);

  const label = (value: string) => (KNOWN_VALUES.has(value) ? t(`values.${value}`) : value);
  const cell = (value: string) => `${SYMBOLS[value] ?? "?"} ${label(value)}`;

  return (
    <section aria-labelledby="health-heading">
      <h2 id="health-heading">{t("heading")}</h2>
      {state.kind === "checking" && <p role="status">{t("checking")}</p>}
      {state.kind === "notConfigured" && <p role="alert">{t("notConfigured")}</p>}
      {state.kind === "unreachable" && (
        <>
          <p role="alert">{cell("unreachable")}</p>
          <p className="muted">{t("unreachable")}</p>
        </>
      )}
      {state.kind === "loaded" && (
        <table className="status-table">
          <tbody>
            <tr>
              <th scope="row">{t("overall")}</th>
              <td>{cell(state.health.status)}</td>
            </tr>
            <tr>
              <th scope="row">{t("database")}</th>
              <td>{cell(state.health.checks.database)}</td>
            </tr>
            <tr>
              <th scope="row">{t("ephemerisFiles")}</th>
              <td>{cell(state.health.checks.ephemeris_files)}</td>
            </tr>
            <tr>
              <th scope="row">{t("libraryMount")}</th>
              <td>{cell(state.health.checks.library_mount)}</td>
            </tr>
            <tr>
              <th scope="row">{t("aiFeatures")}</th>
              <td>{cell(state.health.ai_enabled ? "enabled" : "disabled")}</td>
            </tr>
          </tbody>
        </table>
      )}
    </section>
  );
}

import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";

import { HealthStatus } from "../components/HealthStatus";
import en from "../messages/en.json";
import hi from "../messages/hi.json";

function renderHealth(locale: "en" | "hi", apiBase = "http://api.test/api/v1") {
  const messages = locale === "en" ? en : hi;
  return render(
    <NextIntlClientProvider locale={locale} messages={messages}>
      <HealthStatus apiBase={apiBase} />
    </NextIntlClientProvider>,
  );
}

function mockFetch(body: unknown, status = 200) {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ status, json: () => Promise.resolve(body) }));
}

afterEach(() => vi.unstubAllGlobals());

const okBody = {
  status: "ok",
  checks: { database: "ok", ephemeris_files: "not_configured", library_mount: "not_configured" },
  ai_enabled: false,
};

describe("HealthStatus", () => {
  it("shows each check as symbol plus text, in English", async () => {
    mockFetch(okBody);
    renderHealth("en");
    // Two rows read OK: the API itself and the database.
    expect(await screen.findAllByText("✓ OK", { selector: "td" })).toHaveLength(2);
    expect(screen.getAllByText("– Not configured yet")).toHaveLength(2);
    expect(screen.getByText("– Off")).toBeInTheDocument();
  });

  it("shows the same facts in Hindi", async () => {
    mockFetch(okBody);
    renderHealth("hi");
    expect(await screen.findAllByText("✓ ठीक है", { selector: "td" })).toHaveLength(2);
    expect(screen.getByText("– बंद")).toBeInTheDocument();
  });

  it("shows a degraded API honestly, not as OK", async () => {
    mockFetch(
      { ...okBody, status: "degraded", checks: { ...okBody.checks, database: "error" } },
      503,
    );
    renderHealth("en");
    expect(await screen.findByText("! Degraded")).toBeInTheDocument();
    expect(screen.getByText("✗ Error")).toBeInTheDocument();
  });

  it("shows an unreachable message when the request fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("network down")));
    renderHealth("en");
    expect(await screen.findByRole("alert")).toHaveTextContent("✗ Unreachable");
  });

  it("reports a missing API address instead of guessing one", () => {
    renderHealth("en", "");
    expect(screen.getByRole("alert")).toHaveTextContent("no API address");
  });
});

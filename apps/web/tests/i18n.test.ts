import { describe, expect, it } from "vitest";

import en from "../messages/en.json";
import hi from "../messages/hi.json";

type Tree = { [key: string]: string | Tree };

function leafKeys(tree: Tree, prefix = ""): string[] {
  return Object.entries(tree).flatMap(([key, value]) =>
    typeof value === "string" ? [`${prefix}${key}`] : leafKeys(value, `${prefix}${key}.`),
  );
}

function leaves(tree: Tree, prefix = ""): Record<string, string> {
  return Object.fromEntries(
    Object.entries(tree).flatMap(([key, value]) =>
      typeof value === "string"
        ? [[`${prefix}${key}`, value]]
        : Object.entries(leaves(value, `${prefix}${key}.`)),
    ),
  );
}

describe("message catalogues (docs/testing.md section 3: CI fails on missing keys)", () => {
  it("hi.json has exactly the keys of en.json", () => {
    expect(leafKeys(hi as Tree).sort()).toEqual(leafKeys(en as Tree).sort());
  });

  it("no message is empty", () => {
    for (const [name, catalogue] of [
      ["en", en],
      ["hi", hi],
    ] as const) {
      for (const [key, value] of Object.entries(leaves(catalogue as Tree))) {
        expect(value.trim(), `${name}:${key}`).not.toBe("");
      }
    }
  });

  it("Hindi messages are written in Devanagari (apart from deliberate Latin names)", () => {
    const allowedLatin = new Set(["Home.english"]); // the language's own English name
    for (const [key, value] of Object.entries(leaves(hi as Tree))) {
      if (allowedLatin.has(key)) continue;
      expect(/[ऀ-ॿ]/.test(value), `hi:${key} has no Devanagari`).toBe(true);
    }
  });
});

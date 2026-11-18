// CI guard: fail on high/critical npm advisories unless they are listed, with a reason and an
// unexpired review date, in apps/web/audit-exceptions.json (docs/security.md section 8).
// Usage: node scripts/check-npm-audit.mjs
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const webDir = join(dirname(fileURLToPath(import.meta.url)), "..", "apps", "web");
const today = new Date().toISOString().slice(0, 10);

let raw;
try {
  raw = execFileSync("npm", ["audit", "--json"], { cwd: webDir, shell: true, encoding: "utf8" });
} catch (error) {
  // npm audit exits non-zero when it finds vulnerabilities; the JSON is still on stdout.
  raw = error.stdout;
}
const report = JSON.parse(raw);
if (report.error) {
  console.error("npm audit failed:", report.error.summary ?? report.error);
  process.exit(2);
}

const { exceptions } = JSON.parse(readFileSync(join(webDir, "audit-exceptions.json"), "utf8"));
const byUrl = new Map(exceptions.map((e) => [e.advisory, e]));

const advisories = new Map();
for (const vulnerability of Object.values(report.vulnerabilities ?? {})) {
  for (const via of vulnerability.via) {
    if (typeof via === "object" && ["high", "critical"].includes(via.severity)) {
      advisories.set(via.url, { package: via.name, title: via.title, severity: via.severity });
    }
  }
}

let failed = false;
for (const [url, info] of advisories) {
  const exception = byUrl.get(url);
  if (!exception) {
    console.error(`NOT ALLOWED  ${info.severity}  ${info.package}: ${info.title}  ${url}`);
    failed = true;
  } else if (exception.review_by < today) {
    console.error(`EXPIRED EXCEPTION (review_by ${exception.review_by})  ${info.package}  ${url}`);
    failed = true;
  } else {
    console.log(`excepted until ${exception.review_by}  ${info.package}: ${info.title}`);
  }
}
for (const url of byUrl.keys()) {
  if (!advisories.has(url)) {
    console.log(`note: exception no longer needed, remove it from audit-exceptions.json: ${url}`);
  }
}

if (failed) process.exit(1);
console.log(`npm audit check: ok (${advisories.size} high/critical advisory, all excepted)`);

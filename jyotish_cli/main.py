"""`jyotish` entry point.

    jyotish rules validate [--against REF] [--format json] [--strict]
    jyotish rules list
    jyotish rules hash <RULE_ID|file>
    jyotish rules seal <RULE_ID|file>
    jyotish rules approve <RULE_ID> --version N [--reject --reason TEXT]   (interactive terminal only)

Exit codes: 0 ok, 1 validation errors (or warnings with --strict), 2 usage or tool error.
"""

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from datetime import date
from pathlib import Path

from knowledge.rulebase.approval import ApprovalError, apply_owner_decision, seal_file
from knowledge.rulebase.enums import NAMESPACE_DIR, CitationRelation
from knowledge.rulebase.hashing import version_hash
from knowledge.rulebase.history import HistoryError, check_append_only
from knowledge.rulebase.lifecycle import current_status, latest_version, served_version
from knowledge.rulebase.loader import RulebasePaths, load_rulebase
from knowledge.rulebase.validator import validate_loaded
from knowledge.rulebase.yamlio import YamlError, load_yaml_text

Printer = Callable[[str], None]


def find_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "pyproject.toml").is_file() and (candidate / "knowledge").is_dir():
            return candidate
    return start


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jyotish", description="Jyotish Research Platform tools")
    top = parser.add_subparsers(dest="group", required=True)
    rules = top.add_parser("rules", help="rule knowledge base")
    sub = rules.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--root",
            type=Path,
            default=None,
            help="repository root (default: found from the current directory)",
        )

    validate = sub.add_parser("validate", help="validate all rule and source records")
    common(validate)
    validate.add_argument(
        "--against",
        metavar="REF",
        help="git ref to compare with: recorded history must be append-only",
    )
    validate.add_argument("--format", choices=["text", "json"], default="text")
    validate.add_argument("--strict", action="store_true", help="treat warnings as failures")
    validate.add_argument("--today", help=argparse.SUPPRESS)

    listing = sub.add_parser(
        "list", help="list rules with status and whether runtime retrieval would serve them"
    )
    common(listing)

    for name, text in (
        ("hash", "print the content hash of each version"),
        ("seal", "write missing content_hash values"),
    ):
        p = sub.add_parser(name, help=text)
        common(p)
        p.add_argument("target", help="RULE_ID or path to a rule file")

    approve = sub.add_parser(
        "approve",
        help="OWNER ONLY: approve or reject the latest version (interactive terminal required)",
    )
    common(approve)
    approve.add_argument("rule_id")
    approve.add_argument("--version", type=int, required=True)
    approve.add_argument(
        "--reject", action="store_true", help="record a rejection instead of an approval"
    )
    approve.add_argument("--reason", help="required with --reject")
    approve.add_argument("--note", help="optional note stored with the review")
    return parser


def _resolve(paths: RulebasePaths, target: str) -> Path | None:
    candidate = Path(target)
    if candidate.suffix == ".yaml" and candidate.is_file():
        return candidate
    for directory in NAMESPACE_DIR.values():
        path = paths.rules_dir / directory / f"{target}.yaml"
        if path.is_file():
            return path
    return None


def _cmd_validate(args: argparse.Namespace, paths: RulebasePaths, out: Printer) -> int:
    today = date.fromisoformat(args.today) if args.today else date.today()
    rulebase = load_rulebase(paths)
    report = validate_loaded(rulebase, today=today)
    if args.against:
        try:
            report.findings.extend(check_append_only(rulebase, args.against))
        except HistoryError as problem:
            out(f"error: {problem}")
            return 2
    if args.format == "json":
        out(
            json.dumps(
                {
                    "ok": report.ok and not (args.strict and report.warnings),
                    "rules_checked": report.rules_checked,
                    "sources_checked": report.sources_checked,
                    "findings": [
                        {
                            "code": f.code,
                            "severity": f.severity.value,
                            "rule_id": f.rule_id,
                            "file": f.file,
                            "message": f.message,
                        }
                        for f in report.findings
                    ],
                },
                indent=2,
            )
        )
    else:
        for finding in report.findings:
            out(finding.format())
        out(
            f"rules checked: {report.rules_checked}, sources checked: {report.sources_checked}, "
            f"errors: {len(report.errors)}, warnings: {len(report.warnings)}"
            + (f", history checked against {args.against}" if args.against else "")
        )
        out(
            "RESULT: " + ("OK" if report.ok and not (args.strict and report.warnings) else "FAILED")
        )
    if report.errors or (args.strict and report.warnings):
        return 1
    return 0


def _cmd_list(paths: RulebasePaths, out: Printer) -> int:
    rulebase = load_rulebase(paths)
    if not rulebase.rules:
        out("no rule records found")
        return 0
    out(
        f"{'RULE_ID':14} {'NAMESPACE':10} {'TYPE':24} {'LATEST':7} {'STATUS':20} SERVED_IN_RETRIEVAL"
    )
    for rule_id in sorted(rulebase.rules):
        model = rulebase.rules[rule_id].model
        status = current_status(model)
        served = served_version(model)
        out(
            f"{rule_id:14} {model.namespace.value:10} {model.rule_type.value:24} v{latest_version(model):<6} "
            f"{status.value if status else '-':20} {'v' + str(served) if served else 'no'}"
        )
    out("(retrieval additionally requires the whole rulebase to validate with zero errors)")
    return 0


def _cmd_hash(args: argparse.Namespace, paths: RulebasePaths, out: Printer, *, seal: bool) -> int:
    path = _resolve(paths, args.target)
    if path is None:
        out(f"error: no rule file found for {args.target!r}")
        return 2
    if seal:
        try:
            sealed = seal_file(path)
        except ApprovalError as problem:
            out(f"error: {problem}")
            return 2
        out(
            f"sealed versions: {sealed}"
            if sealed
            else "nothing to seal (every version already has a content_hash)"
        )
        return 0
    try:
        raw = load_yaml_text(path.read_text(encoding="utf-8"))
    except YamlError as problem:
        out(f"error: {problem}")
        return 2
    for entry in raw.get("versions", []):
        computed = version_hash(str(raw.get("rule_id")), int(entry["version"]), entry["content"])
        stored = entry.get("content_hash")
        note = "" if stored == computed else f"  (stored: {stored})"
        out(f"v{entry['version']}: {computed}{note}")
    return 0


def _cmd_approve(
    args: argparse.Namespace,
    paths: RulebasePaths,
    out: Printer,
    interactive: bool,
    ask: Callable[[str], str],
) -> int:
    if not interactive:
        out(
            "error: `jyotish rules approve` needs an interactive terminal. Run it yourself; scripts and AI agents cannot approve rules."
        )
        return 2
    rulebase = load_rulebase(paths)
    loaded = rulebase.rules.get(args.rule_id)
    if loaded is None:
        out(f"error: rule {args.rule_id} not found or does not parse")
        return 2
    entry = next((e for e in loaded.model.versions if e.version == args.version), None)
    content = loaded.contents.get(args.version)
    if entry is None or content is None:
        out(f"error: version {args.version} not found")
        return 2
    out(
        f"Rule {args.rule_id} version {args.version}  ({loaded.model.namespace.value}, {loaded.model.rule_type.value})"
    )
    out(f"Title:     {content.title}")
    out(f"Statement: {content.statement}")
    out(f"Hash:      {entry.content_hash}")
    for citation in content.citations:
        marker = (
            "SUPPORTS"
            if citation.relation is CitationRelation.SUPPORTS
            else citation.relation.value
        )
        out(
            f"  [{marker}] {citation.citation_id}  page={citation.page} chapter={citation.chapter} passage={citation.passage_review_status.value}"
        )
        out(f'      "{citation.quote}"')
    for relation in content.relations:
        out(f"  relation: {relation.kind.value} {relation.target}")
    for note in content.ambiguity_notes:
        out(f"  ambiguity: {note}")
    action = "REJECT" if args.reject else "APPROVE"
    out("")
    out(
        "This records YOUR source approval of the text above against the cited passages. It is not expert "
        "validation of the Jyotish content."
        if action == "APPROVE"
        else "This records your rejection of this version."
    )
    typed = ask(
        f"Type the rule ID ({args.rule_id}) to {action.lower()}, or press Enter to cancel: "
    ).strip()
    if not typed:
        out("cancelled; nothing changed")
        return 1
    try:
        written = apply_owner_decision(
            paths,
            args.rule_id,
            args.version,
            action,  # type: ignore[arg-type]
            interactive=interactive,
            typed_confirmation=typed,
            reason=args.reason,
            notes=args.note,
        )
    except ApprovalError as problem:
        out(f"refused: {problem}")
        return 1
    out(f"recorded {action} for {args.rule_id} v{args.version} in {written}")
    return 0


def run(
    argv: Sequence[str] | None = None,
    *,
    out: Printer = print,
    interactive: bool | None = None,
    ask: Callable[[str], str] = input,
) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    root = args.root if args.root is not None else find_root(Path.cwd())
    paths = RulebasePaths.from_root(root.resolve())
    if interactive is None:
        interactive = sys.stdin.isatty() and sys.stdout.isatty()
    if args.group == "rules":
        if args.command == "validate":
            return _cmd_validate(args, paths, out)
        if args.command == "list":
            return _cmd_list(paths, out)
        if args.command in ("hash", "seal"):
            return _cmd_hash(args, paths, out, seal=args.command == "seal")
        if args.command == "approve":
            return _cmd_approve(args, paths, out, interactive, ask)
    parser.error("unknown command")
    return 2


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()

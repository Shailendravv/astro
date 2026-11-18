"""The `jyotish rules ...` commands: exit codes, output, and the owner-only approval gate."""

import json
import subprocess
from pathlib import Path

from rulebase_builders import (
    TODAY,
    interpretive_content,
    make_rule,
    rule_path,
    write_repo,
)

from jyotish_cli.main import find_root, run
from knowledge.rulebase.lifecycle import current_status
from knowledge.rulebase.loader import load_rulebase


def cli(*argv, interactive=False, ask=None):
    lines: list[str] = []
    code = run(
        [*argv],
        out=lines.append,
        interactive=interactive,
        ask=ask or (lambda _prompt: ""),
    )
    return code, "\n".join(lines)


def test_validate_ok_exit_zero(tmp_path):
    write_repo(tmp_path, [make_rule(status="VERIFIED")])
    code, out = cli("rules", "validate", "--root", str(tmp_path), "--today", TODAY.isoformat())
    assert code == 0
    assert "RESULT: OK" in out
    assert "rules checked: 1" in out


def test_validate_reports_errors_with_code_rule_and_file_and_exits_one(tmp_path):
    raw = make_rule(status="VERIFIED")
    raw["versions"][0]["content"]["statement"] = "Edited after approval."
    write_repo(tmp_path, [raw])
    code, out = cli("rules", "validate", "--root", str(tmp_path), "--today", TODAY.isoformat())
    assert code == 1
    assert "VERSION-HASH [PAR-ASP-0001]" in out
    assert "parashari/PAR-ASP-0001.yaml" in out
    assert "RESULT: FAILED" in out


def test_validate_json_output_is_machine_readable(tmp_path):
    write_repo(tmp_path, [make_rule(status="DRAFT", content={"title": "t"})])
    code, out = cli(
        "rules",
        "validate",
        "--root",
        str(tmp_path),
        "--format",
        "json",
        "--today",
        TODAY.isoformat(),
    )
    data = json.loads(out)
    assert code == 0
    assert data["ok"] is True
    assert data["rules_checked"] == 1


def test_strict_turns_warnings_into_failure(tmp_path):
    uncatalogued = {"citation_id": "SRC-UNLISTED:ch1:v1", "relation": "SUPPORTS"}
    raw = make_rule(status="DRAFT", content=interpretive_content(citations=[uncatalogued]))
    write_repo(tmp_path, [raw])
    args = ("rules", "validate", "--root", str(tmp_path), "--today", TODAY.isoformat())
    assert cli(*args)[0] == 0
    assert cli(*args, "--strict")[0] == 1


def test_validate_against_a_ref_checks_append_only_history(tmp_path):
    raw = make_rule(status="VERIFIED")
    paths = write_repo(tmp_path, [raw])
    git = [
        "git",
        "-c",
        "user.name=T",
        "-c",
        "user.email=t@example.invalid",
        "-c",
        "commit.gpgsign=false",
        "-C",
        str(tmp_path),
    ]
    subprocess.run([*git, "init", "-q", "-b", "main"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-q", "-m", "base"], check=True)
    base = (
        "rules",
        "validate",
        "--root",
        str(tmp_path),
        "--today",
        TODAY.isoformat(),
        "--against",
        "HEAD",
    )
    assert cli(*base)[0] == 0
    rule_path(paths, raw).unlink()
    code, out = cli(*base)
    assert code == 1
    assert "HIST-DELETED" in out


def test_validate_against_unknown_ref_is_a_tool_error_exit_two(tmp_path):
    write_repo(tmp_path, [])
    code, out = cli("rules", "validate", "--root", str(tmp_path), "--against", "nope")
    assert code == 2
    assert "cannot resolve" in out


def test_list_shows_status_and_whether_retrieval_would_serve_the_rule(tmp_path):
    write_repo(
        tmp_path,
        [
            make_rule("PAR-ASP-0001", status="VERIFIED"),
            make_rule("PAR-ASP-0002", status="PROVISIONAL"),
        ],
    )
    code, out = cli("rules", "list", "--root", str(tmp_path))
    assert code == 0
    lines = {line.split()[0]: line for line in out.splitlines() if line.startswith("PAR-")}
    assert "VERIFIED" in lines["PAR-ASP-0001"] and lines["PAR-ASP-0001"].rstrip().endswith("v1")
    assert "PROVISIONAL" in lines["PAR-ASP-0002"] and lines["PAR-ASP-0002"].rstrip().endswith("no")


def test_list_on_an_empty_rulebase(tmp_path):
    write_repo(tmp_path, [])
    code, out = cli("rules", "list", "--root", str(tmp_path))
    assert (code, out) == (0, "no rule records found")


def test_hash_prints_each_version_hash_and_flags_a_stored_mismatch(tmp_path):
    raw = make_rule()
    raw["versions"][0]["content_hash"] = "sha256:" + "0" * 64
    write_repo(tmp_path, [raw])
    code, out = cli("rules", "hash", "PAR-ASP-0001", "--root", str(tmp_path))
    assert code == 0
    assert out.startswith("v1: sha256:")
    assert "(stored: sha256:000" in out


def test_seal_command_and_unknown_target(tmp_path):
    raw = make_rule()
    del raw["versions"][0]["content_hash"]
    write_repo(tmp_path, [raw])
    assert (
        cli("rules", "seal", "PAR-ASP-0001", "--root", str(tmp_path))[1] == "sealed versions: [1]"
    )
    code, out = cli("rules", "seal", "PAR-ZZZ-9999", "--root", str(tmp_path))
    assert code == 2 and "no rule file" in out


def test_approve_refuses_without_a_terminal_and_changes_nothing(tmp_path):
    paths = write_repo(tmp_path, [make_rule(status="PROVISIONAL")])
    before = rule_path(paths, make_rule()).read_bytes()
    code, out = cli(
        "rules",
        "approve",
        "PAR-ASP-0001",
        "--version",
        "1",
        "--root",
        str(tmp_path),
        interactive=False,
    )
    assert code == 2
    assert "interactive terminal" in out
    assert rule_path(paths, make_rule()).read_bytes() == before


def test_approve_shows_the_evidence_and_records_on_the_typed_rule_id(tmp_path):
    paths = write_repo(tmp_path, [make_rule(status="PROVISIONAL")])
    prompts: list[str] = []

    def ask(prompt: str) -> str:
        prompts.append(prompt)
        return "PAR-ASP-0001"

    code, out = cli(
        "rules",
        "approve",
        "PAR-ASP-0001",
        "--version",
        "1",
        "--root",
        str(tmp_path),
        interactive=True,
        ask=ask,
    )
    assert code == 0, out
    assert "Synthetic quote used only in tests." in out  # the owner sees the quoted evidence
    assert "not expert validation" in out  # and is told what approval does and does not mean
    assert "recorded APPROVE" in out
    assert len(prompts) == 1
    assert current_status(load_rulebase(paths).rules["PAR-ASP-0001"].model) == "VERIFIED"


def test_approve_cancelled_by_empty_input_changes_nothing(tmp_path):
    paths = write_repo(tmp_path, [make_rule(status="PROVISIONAL")])
    code, out = cli(
        "rules",
        "approve",
        "PAR-ASP-0001",
        "--version",
        "1",
        "--root",
        str(tmp_path),
        interactive=True,
        ask=lambda _p: "",
    )
    assert code == 1 and "cancelled" in out
    assert current_status(load_rulebase(paths).rules["PAR-ASP-0001"].model) == "PROVISIONAL"


def test_approve_with_wrong_confirmation_is_refused(tmp_path):
    paths = write_repo(tmp_path, [make_rule(status="PROVISIONAL")])
    code, out = cli(
        "rules",
        "approve",
        "PAR-ASP-0001",
        "--version",
        "1",
        "--root",
        str(tmp_path),
        interactive=True,
        ask=lambda _p: "yes",
    )
    assert code == 1 and "refused" in out
    assert current_status(load_rulebase(paths).rules["PAR-ASP-0001"].model) == "PROVISIONAL"


def test_reject_via_cli_needs_a_reason(tmp_path):
    paths = write_repo(tmp_path, [make_rule(status="PROVISIONAL")])
    common = (
        "rules",
        "approve",
        "PAR-ASP-0001",
        "--version",
        "1",
        "--reject",
        "--root",
        str(tmp_path),
    )
    code, out = cli(*common, interactive=True, ask=lambda _p: "PAR-ASP-0001")
    assert code == 1 and "reason" in out
    code, out = cli(
        *common, "--reason", "Misread passage", interactive=True, ask=lambda _p: "PAR-ASP-0001"
    )
    assert code == 0
    assert current_status(load_rulebase(paths).rules["PAR-ASP-0001"].model) == "REJECTED"


def test_approve_unknown_rule_or_version(tmp_path):
    write_repo(tmp_path, [make_rule(status="PROVISIONAL")])
    assert (
        cli(
            "rules",
            "approve",
            "PAR-ASP-0099",
            "--version",
            "1",
            "--root",
            str(tmp_path),
            interactive=True,
        )[0]
        == 2
    )
    assert (
        cli(
            "rules",
            "approve",
            "PAR-ASP-0001",
            "--version",
            "9",
            "--root",
            str(tmp_path),
            interactive=True,
        )[0]
        == 2
    )


def test_find_root_walks_up_to_the_repository(tmp_path):
    (tmp_path / "knowledge").mkdir()
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    assert find_root(nested) == tmp_path
    assert find_root(Path(tmp_path.anchor)) == Path(tmp_path.anchor)

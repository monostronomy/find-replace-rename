import json
import os
import re
import sys
import tempfile
from pathlib import Path
import subprocess

# Ensure we can import the module under test
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYS_PATH_ADDED = False
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
    SYS_PATH_ADDED = True

import file_renamer  # noqa: E402


def create_demo_tree(base: Path) -> None:
    (base / "Reports").mkdir(parents=True, exist_ok=True)
    (base / "Report-123.txt").write_text("")
    (base / "Report-456.pdf").write_text("")
    (base / "draft_note.txt").write_text("")
    (base / "Reports" / "Report-789.txt").write_text("")


def test_find_matches_literal(tmp_path: Path):
    create_demo_tree(tmp_path)
    matches = file_renamer.find_matches(
        root=str(tmp_path),
        find_term="Report",
        case_sensitive=False,
        include_dirs=False,
        exts=None,
        regex=False,
    )
    paths = {Path(p) for p, is_dir in matches if not is_dir}
    # Should include both txt and pdf Report files, but not draft_note.txt
    assert (tmp_path / "Report-123.txt") in paths
    assert (tmp_path / "Report-456.pdf") in paths
    assert (tmp_path / "Reports" / "Report-789.txt") in paths
    assert (tmp_path / "draft_note.txt") not in paths


def test_find_matches_regex_with_ext_and_dirs(tmp_path: Path):
    create_demo_tree(tmp_path)
    matches = file_renamer.find_matches(
        root=str(tmp_path),
        find_term=r"(?i)report",
        case_sensitive=False,
        include_dirs=True,  # include directories named "Reports"
        exts=[".txt"],
        regex=True,
    )
    # Only .txt files and the Reports directory (if matching)
    files = {Path(p) for p, is_dir in matches if not is_dir}
    dirs = {Path(p) for p, is_dir in matches if is_dir}
    assert (tmp_path / "Report-123.txt") in files
    assert (tmp_path / "Reports" / "Report-789.txt") in files
    assert (tmp_path / "Report-456.pdf") not in files
    # Directory name should match when include_dirs=True and regex matches
    assert (tmp_path / "Reports") in dirs


def test_find_only_integration_jsonl(tmp_path: Path):
    create_demo_tree(tmp_path)
    # Run script as a subprocess with cwd at tmp_path so logs are created here
    script = str(PROJECT_ROOT / "file_renamer.py")
    cmd = [sys.executable, script, "--find-only", "--json-log", str(tmp_path), "Report"]
    result = subprocess.run(cmd, cwd=str(tmp_path), capture_output=True, text=True)
    assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"

    # Locate the JSONL log created in tmp_path
    logs = sorted(tmp_path.glob("renamed*.jsonl"))
    assert logs, "Expected a JSONL log file to be created"
    log_path = logs[-1]

    # Count 'action': 'find' entries
    find_count = 0
    summary_found = False
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("action") == "find":
                find_count += 1
            if obj.get("action") == "summary":
                summary_found = True
                # Cross-check the summary totals are consistent
                assert obj.get("renamed") == 0
                assert obj.get("errors") == 0
    assert find_count >= 2  # at least the two Report* files; may be more depending on matching
    assert summary_found

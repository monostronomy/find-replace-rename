import json
import sys
from pathlib import Path
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def create_demo_tree(base: Path) -> None:
    (base / "Reports").mkdir(parents=True, exist_ok=True)
    (base / "Report-123.txt").write_text("")
    (base / "Report-456.pdf").write_text("")
    (base / "draft_note.txt").write_text("")
    (base / "Reports" / "Report-789.txt").write_text("")


def test_dry_run_jsonl_counts(tmp_path: Path):
    create_demo_tree(tmp_path)
    script = str(PROJECT_ROOT / "file_renamer.py")
    # Provide 'y' to confirm plan
    cmd = [sys.executable, script, "--dry-run", "--json-log", str(tmp_path), "Report", "Rpt"]
    result = subprocess.run(cmd, cwd=str(tmp_path), input="y\n", text=True, capture_output=True)
    assert result.returncode == 0, result.stderr

    logs = sorted(tmp_path.glob("renamed*.jsonl"))
    assert logs, "Expected JSONL log file"
    log_path = logs[-1]

    dry_renames = 0
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("action") == "dry_run_rename":
                dry_renames += 1
    # We expect three Report* files in demo tree
    assert dry_renames == 3


def test_approve_each_dry_run_selection(tmp_path: Path):
    create_demo_tree(tmp_path)
    script = str(PROJECT_ROOT / "file_renamer.py")
    # Approve-each: first 'a' at plan, then y, n, n per item
    cmd = [sys.executable, script, "--dry-run", str(tmp_path), "Report", "Rpt"]
    # Send 'a' to enter approve-each, then respond to three items
    user_input = "a\n" + "y\n" + "n\n" + "n\n"
    result = subprocess.run(cmd, cwd=str(tmp_path), input=user_input, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    # In dry-run + approve-each, only approved items are counted as renamed
    # Verify the summary reflects exactly one item was processed
    assert "Renamed     : 1" in result.stdout

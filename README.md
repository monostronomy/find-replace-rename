# Recursive File Renamer (Windows-friendly)

[![CI](https://github.com/monostronomy/find-replace-rename/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/monostronomy/find-replace-rename/actions)

A robust Python script to recursively search and rename files (and optionally directories) with flexible find/replace rules. Supports interactive prompts and CLI usage, dry-run previews, name-collision handling, backups, and both human-readable and JSONL structured logging.

## Features

- Interactive and CLI modes
- Default case-insensitive matching; `--cs` toggles case-sensitive
- Files only by default; `--include-dirs` optionally includes directories
- Name collisions resolved by appending numeric suffixes with NO SPACE: `(1)`, `(2)`, `(3)`, ... before the extension
- Optional `--dry-run` to preview changes
- Optional extension filter via `--ext ".pdf,.txt"`
- Approve-each mode (`a`) to confirm items one-by-one
- Verbose, dated text log (`renamed.mm.dd.YYYY.txt`) and structured JSONL log (`renamed.mm.dd.YYYY.jsonl`)
- Optional `--backup` to create a `.bak` copy of each original file before renaming (with its own collision handling)
- Optional `--regex` to enable regex-based matching and backreferences in replacement

## Requirements

- Python 3.8+
- Standard library only (no external dependencies)

## Installation

1. Download the repository or copy `file_renamer.py` to a folder of your choice (e.g., `C:\Tools\find-replace-rename`).
2. Ensure Python is installed and available in your PATH (`python --version`).

## Quick Start

Rename all occurrences of `foo` to `bar` under `D:\Projects`:

```powershell

python file_renamer.py "D:\Projects" "foo" "bar"
```

Remove a term by providing an empty replace value (use quotes to pass empty string):

```powershell
python file_renamer.py "C:\" "(Z-Library)" ""
```

Preview first (no changes made):

```powershell
python file_renamer.py "D:\Projects" "foo" "bar" --dry-run
```

## CLI Usage

```text
usage: file_renamer.py [-h] [--cs] [--dry-run] [--include-dirs] [--ext EXT] [--v] [--backup] [--json-log] [--regex] [--find-only] [location] [find] [replace]

Recursively find and rename files (and optionally directories).

positional arguments:
  location        Root path to search (drive like C:\ or a folder)
  find            Find term (use quotes for multiple words)
  replace         Replace-with term (omit to remove find term)

options:
  -h, --help      show this help message and exit
  --cs            Case-sensitive match (default is case-insensitive)
  --dry-run       Preview changes without renaming
  --include-dirs  Also rename directories (in addition to files)
  --ext EXT       Comma-separated list of file extensions to include, e.g. ".pdf,.txt"
  --v             Verbose logging to a dated log file and console
  --backup        Create backup copy of original files (.bak) before renaming
  --json-log      Write structured JSONL log (renamed.mm.dd.YYYY.jsonl)
  --regex         Use regular expression for find term; replacement supports backreferences like \1
  --find-only     Search only: list and log matches without renaming
```

## Examples

- Case-sensitive replace:

```Powershell

python file_renamer.py "D:\Projects" "foo" "bar" --cs

```

- Include directories in rename operations:

```Powershell
python file_renamer.py "D:\Projects" "foo" "bar" --include-dirs

```

- Filter to only PDF and TXT files (case-insensitive extensions):

```powershell

python file_renamer.py "D:\Projects" "foo" "bar" --ext ".pdf,.txt"

```

- Approve each change (answer `a` at the confirmation prompt), or run fully interactive with prompts by omitting positionals:

```powershell

python file_renamer.py --dry-run --ext ".pdf,.txt"

### Regex mode (`--regex`)

When `--regex` is enabled, the find term is treated as a regular expression. Default matching is case-insensitive unless you pass `--cs`.

- Replace digits with bracketed digits (dry run):

```powershell
python file_renamer.py "D:\Projects" --regex "(\d+)" "[\\1]" --dry-run
```

- Case-sensitive regex with capture group reuse:

```powershell
python file_renamer.py "D:\Projects" --regex --cs "Report-(\d+)" "Report-\\1-Final"
```

- Combine with extension filter:

```powershell
python file_renamer.py "D:\Projects" --regex --ext ".pdf,.txt" "(?i)draft" "final" --dry-run
```

Escaping notes (PowerShell):

- Use single quotes around the replacement when using backreferences to avoid `$` expansion, e.g. `'$1_new'`.
- If using double quotes, escape the dollar: ``"`$1_new"``.
- Backslashes in patterns or replacements may require doubling.

## Name Collision Handling

If the desired destination already exists, the script appends a numeric suffix before the extension with NO SPACE:

- `Report.pdf` → `Report(1).pdf` → `Report(2).pdf`, etc.
Backups also use the same no-space suffix: `Report.pdf.bak`, `Report.pdf.bak(1)`, `Report.pdf.bak(2)`, ...

## Backups (`--backup`)

- When enabled, a `.bak` copy is created before renaming each file.
- Backups are only for files (not directories).
- Backup collisions are resolved by appending `(1)`, `(2)`, etc., with no space.

## Dry Run (`--dry-run`)

- Shows what would change without doing any filesystem writes.
- Works with all other options; you can also combine with `--json-log` for a machine-readable preview.

## Logging

- Text log: `renamed.mm.dd.YYYY.txt` (collision-safe)
- JSONL log: `renamed.mm.dd.YYYY.jsonl` (collision-safe) when `--json-log` is provided

### JSONL Entry Examples

Each line is a JSON object. Example actions:

```json
{"ts":"2025-08-23T03:19:43Z","action":"dry_run_rename","src":"D:/a/old.txt","dst":"D:/a/new.txt","is_dir":false,"status":"ok","case_sensitive":false,"include_dirs":false,"dry_run":true,"backup":false,"regex":true,"exts":[]}
{"ts":"2025-08-23T03:19:43-04:00","action":"backup","src":"D:/a/old.txt","dst":"D:/a/old.txt.bak","is_dir":false,"status":"ok"}
{"ts":"2025-08-23T03:19:43-04:00","action":"rename","src":"D:/a/old.txt","dst":"D:/a/new.txt","is_dir":false,"status":"ok"}
{"ts":"2025-08-23T03:19:43-04:00","action":"error","stage":"backup","src":"D:/a/old.txt","dst":"D:/a/old.txt.bak","error":"Permission denied"}
{"ts":"2025-08-23T03:19:43-04:00","action":"summary","found":42,"renamed":40,"skipped":2}

```

## Interactive Mode & Approval

- If you run without positional args, the script prompts for location, find, and replace.
- After gathering inputs (from CLI or prompts), the script prints a summary and asks:

  - `y/yes`: proceed
  - `n/no`: exit
  - `a`: approve each item one-by-one
  - `c`: change inputs (pre-filled with previous responses)

## Windows 11: Add Script Folder to PATH

So you can run the script from any directory as `file_renamer.py` or `python file_renamer.py`:

1. Choose a permanent folder for the script, e.g. `C:\Tools\file-renamer`.
2. Move or save `file_renamer.py` there.
3. Press `Win` key, type "Environment Variables", and open "Edit the system environment variables".
4. In the System Properties window, click "Environment Variables...".
5. Under "User variables" (or "System variables" if you want it for all users), select `Path` → "Edit".
6. Click "New" and add the folder path, e.g. `C:\Tools\file-renamer`.
7. Click OK on all dialogs to save.
8. Open a new PowerShell or Command Prompt window (important to reload PATH), and run:

   ```powershell

   file_renamer.py --help
   # or explicitly
   python file_renamer.py --help
   ```

Tip: You can also create a small wrapper `file_renamer.cmd` in that same folder with:

```bat

@echo off
python "%~dp0file_renamer.py" %*
```

With your PATH set, you can then invoke `file_renamer` directly from anywhere.

## Safety Notes

- Always start with `--dry-run` to review changes.
- Use `--backup` for an extra safety net before renaming.
- Long/locked paths and permissions issues can cause failures; errors are logged.

## Development

- Standard library: `argparse`, `os`, `shutil`, `re`, `sys`, `datetime`, `json`.
- No external dependencies.
- Tested primarily on Windows. Should also work cross-platform where permissions/path rules allow.

## Testing

- Run the test suite with pytest:

```powershell
python -m pytest -q
```

- Try the find-only demo script (PowerShell):

```powershell
scripts/demo_findonly.ps1
```

Continuous Integration:

- GitHub Actions runs the tests on Windows and Linux for pushes and pull requests.


## License

MIT License

#!/usr/bin/env python3
"""
Recursive File Renamer

Features:
- Interactive and CLI modes
- Default case-insensitive find/replace; --cs toggles case-sensitive
- Files only by default; optional --include-dirs to rename directories too
- Name collisions resolved by appending "(1)", "(2)", etc., before file extension
- Optional --dry-run to preview changes without applying them
- Optional --ext ".pdf,.txt" to limit by extensions (case-insensitive)
- Progress indicators and approve-each mode ('a')
- Verbose logging with --v to a dated log file: renamed.mm.dd.yyyy.txt (with collision handling)
- Optional --backup to create a .bak copy (with collision handling) before renaming files

CLI usage examples:
  python file_renamer.py "C:\\" "(Z-Library)" ""         # remove term from all files under C:\ (case-insensitive)
  python file_renamer.py "D:\\Projects" "foo" "bar"       # replace foo->bar
  python file_renamer.py "D:\\Projects" "foo" --cs        # case-sensitive, remove foo
  python file_renamer.py "(Z-Library)" --cs                 # treat as find-term only; prompt for location, replace
  python file_renamer.py --dry-run --ext ".pdf,.txt"        # interactive prompts, preview only

Confirmation:
- After inputs are gathered (CLI or prompts), script echoes plan and asks: [y/n/a/c]
  y/yes  -> proceed
  n/no   -> exit
  a      -> approve each proposed rename
  c      -> change inputs (re-prompt with previous values pre-filled)
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from typing import Iterable, List, Optional, Tuple
import shutil
import json


def strip_quotes(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = s.strip()
    if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
        return s[1:-1]
    return s


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recursively find and rename files (and optionally directories).",
        add_help=True,
    )
    # Up to three optional positionals: location, find_term, replace_term
    parser.add_argument("location", nargs="?", help="Root path to search (drive like C:\\ or a folder)")
    parser.add_argument("find", nargs="?", help="Find term (use quotes for multiple words)")
    parser.add_argument("replace", nargs="?", help="Replace-with term (omit to remove find term)")

    parser.add_argument("--cs", action="store_true", help="Case-sensitive match (default is case-insensitive)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without renaming",
    )
    parser.add_argument(
        "--include-dirs",
        action="store_true",
        help="Also rename directories (in addition to files)",
    )
    parser.add_argument(
        "--ext",
        type=str,
        default="",
        help="Comma-separated list of file extensions to include, e.g. \".pdf,.txt\"",
    )
    parser.add_argument(
        "--v",
        action="store_true",
        help="Verbose logging to a dated log file and console",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup copy of original files (.bak) before renaming",
    )
    parser.add_argument(
        "--json-log",
        action="store_true",
        help="Write structured JSONL log (renamed.mm.dd.yyyy.jsonl)",
    )
    parser.add_argument(
        "--regex",
        action="store_true",
        help="Use regular expression for find term; replacement supports backreferences like \\1",
    )
    parser.add_argument(
        "--find-only",
        action="store_true",
        help="Search only: list and log matches without renaming",
    )

    args = parser.parse_args(argv)

    # Normalize quotes for find/replace if provided
    args.find = strip_quotes(args.find) if args.find is not None else None
    args.replace = strip_quotes(args.replace) if args.replace is not None else None

    return args


def prompt_with_default(prompt: str, default: Optional[str]) -> str:
    if default is None or default == "":
        return input(f"{prompt}: ").strip()
    else:
        resp = input(f"{prompt} [{default}]: ").strip()
        return default if resp == "" else resp


def confirm_plan(location: str, find_term: str, replace_term: str, case_sensitive: bool, include_dirs: bool, dry_run: bool, exts: List[str], backup: bool, json_log: bool, regex: bool) -> str:
    print("\nPlan:")
    print(f"  Location       : {location}")
    print(f"  Find term      : {find_term!r}")
    print(f"  Replace with   : {replace_term!r}")
    print(f"  Case-sensitive : {'Yes' if case_sensitive else 'No'}")
    print(f"  Regex mode     : {'Yes' if regex else 'No'}")
    print(f"  Include dirs   : {'Yes' if include_dirs else 'No'}")
    print(f"  Dry-run        : {'Yes' if dry_run else 'No'}")
    print(f"  Backup copies  : {'Yes' if backup else 'No'}")
    print(f"  JSON log       : {'Yes' if json_log else 'No'}")
    if exts:
        print(f"  Extensions     : {', '.join(exts)}")
    else:
        print(f"  Extensions     : (all)")
    while True:
        ans = input("Proceed? [y/n/a/c]: ").strip().lower()
        if ans in {"y", "yes", "n", "no", "a", "c"}:
            return ans
        print("Please answer with y, n, a, or c.")


def gather_inputs_interactive(prev: dict | None = None) -> Tuple[str, str, str]:
    prev = prev or {}
    while True:
        location = prompt_with_default("Enter drive/folder to search (e.g., C:\\, D:\\Projects)", prev.get("location"))
        find_term = strip_quotes(prompt_with_default("Enter FIND term", prev.get("find")))
        replace_term = strip_quotes(prompt_with_default("Enter REPLACE-WITH term (leave empty to remove)", prev.get("replace") or ""))
        replace_term = replace_term if replace_term is not None else ""

        ans = confirm_plan(location, find_term, replace_term, prev.get("cs", False), prev.get("include_dirs", False), prev.get("dry_run", False), prev.get("exts", []), prev.get("backup", False), prev.get("json_log", False), prev.get("regex", False))
        if ans in {"y", "yes", "a"}:
            return location, find_term, replace_term
        elif ans in {"n", "no"}:
            print("Aborted by user.")
            sys.exit(0)
        elif ans == "c":
            prev = {"location": location, "find": find_term, "replace": replace_term, **prev}
            continue


def normalize_exts(ext_str: str) -> List[str]:
    if not ext_str:
        return []
    parts = [e.strip() for e in ext_str.split(",") if e.strip()]
    norm = []
    for e in parts:
        if not e.startswith('.'):
            e = '.' + e
        norm.append(e.lower())
    return norm


def name_matches(name: str, term: str, case_sensitive: bool) -> bool:
    if not term:
        return False
    if case_sensitive:
        return term in name
    # case-insensitive contains
    return term.lower() in name.lower()


def ci_replace(text: str, find_term: str, replace_with: str, case_sensitive: bool) -> str:
    if not find_term:
        return text
    if case_sensitive:
        return text.replace(find_term, replace_with)
    # Use regex for case-insensitive replace
    pattern = re.compile(re.escape(find_term), re.IGNORECASE)
    return pattern.sub(replace_with, text)


def regex_replace_name(name: str, pattern: str, repl: str, case_sensitive: bool) -> Tuple[bool, str]:
    """Return (matched, new_name) using regex search/sub. Respects case sensitivity flag."""
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        rx = re.compile(pattern, flags)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {e}")
    matched = rx.search(name) is not None
    if not matched:
        return False, name
    new_name = rx.sub(repl, name)
    return True, new_name


def ensure_log_file(base_dir: str) -> Optional[str]:
    # Create dated log file name like renamed.mm.dd.yyyy.txt with collision handling
    date_str = dt.datetime.now().strftime("%m.%d.%Y")
    base_name = f"renamed.{date_str}.txt"
    path = os.path.join(base_dir, base_name)
    if not os.path.exists(path):
        try:
            with open(path, 'a', encoding='utf-8'):
                pass
            return path
        except Exception:
            return None
    # Collision: append (1), (2), ... before extension (no space)
    root, ext = os.path.splitext(base_name)
    i = 1
    while True:
        trial = os.path.join(base_dir, f"{root}({i}){ext}")
        if not os.path.exists(trial):
            try:
                with open(trial, 'a', encoding='utf-8'):
                    pass
                return trial
            except Exception:
                return None
        i += 1


def find_matches(root: str, find_term: str, case_sensitive: bool, include_dirs: bool, exts: List[str], regex: bool) -> List[Tuple[str, bool]]:
    """Return list of (path, is_dir) for items whose names match the criteria."""
    results: List[Tuple[str, bool]] = []
    for path, is_dir in iter_targets(root, include_dirs):
        if not eligible(path, is_dir, exts):
            continue
        name = os.path.basename(path)
        if regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                if re.search(find_term, name, flags):
                    results.append((path, is_dir))
            except re.error:
                # Invalid regex handled earlier in main
                continue
        else:
            if name_matches(name, find_term, case_sensitive):
                results.append((path, is_dir))
    return results


def ensure_json_log_file(base_dir: str) -> Optional[str]:
    # Create dated JSONL log file like renamed.mm.dd.yyyy.jsonl with collision handling
    date_str = dt.datetime.now().strftime("%m.%d.%Y")
    base_name = f"renamed.{date_str}.jsonl"
    path = os.path.join(base_dir, base_name)
    if not os.path.exists(path):
        try:
            with open(path, 'a', encoding='utf-8'):
                pass
            return path
        except Exception:
            return None
    root, ext = os.path.splitext(base_name)
    i = 1
    while True:
        trial = os.path.join(base_dir, f"{root}({i}){ext}")
        if not os.path.exists(trial):
            try:
                with open(trial, 'a', encoding='utf-8'):
                    pass
                return trial
            except Exception:
                return None
        i += 1


def write_json_log(log_path: Optional[str], payload: dict):
    if not log_path:
        return
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


def iter_targets(root: str, include_dirs: bool) -> Iterable[Tuple[str, bool]]:
    # Yield (path, is_dir)
    for dirpath, dirnames, filenames in os.walk(root):
        if include_dirs:
            for d in dirnames:
                yield os.path.join(dirpath, d), True
        for f in filenames:
            yield os.path.join(dirpath, f), False


def eligible(path: str, is_dir: bool, exts: List[str]) -> bool:
    if is_dir:
        return True  # only constrained by include-dirs switch
    if not exts:
        return True
    _, ext = os.path.splitext(path)
    return ext.lower() in exts


def next_nonconflicting_path(dst: str) -> str:
    if not os.path.exists(dst):
        return dst
    dirn, name = os.path.split(dst)
    root, ext = os.path.splitext(name)
    i = 1
    while True:
        candidate = os.path.join(dirn, f"{root}({i}){ext}")
        if not os.path.exists(candidate):
            return candidate
        i += 1


def backup_nonconflicting_path(src: str) -> str:
    """Return a non-conflicting backup path for src. Uses src + '.bak', then adds (1), (2), ... if needed (no space)."""
    cand = src + ".bak"
    if not os.path.exists(cand):
        return cand
    i = 1
    while True:
        trial = f"{src}.bak({i})"
        if not os.path.exists(trial):
            return trial
        i += 1


def plan_changes(root: str, find_term: str, replace_with: str, case_sensitive: bool, include_dirs: bool, exts: List[str], regex: bool) -> List[Tuple[str, str, bool]]:
    """Return list of (src, dst, is_dir) for items that would be renamed."""
    changes: List[Tuple[str, str, bool]] = []
    for path, is_dir in iter_targets(root, include_dirs):
        if not eligible(path, is_dir, exts):
            continue
        dirn, name = os.path.split(path)
        if regex:
            try:
                matched, new_name = regex_replace_name(name, find_term, replace_with, case_sensitive)
            except ValueError:
                # Invalid regex will be handled earlier; skip here to be safe
                continue
            if not matched:
                continue
        else:
            if not name_matches(name, find_term, case_sensitive):
                continue
            new_name = ci_replace(name, find_term, replace_with, case_sensitive)
        if new_name == name:
            continue
        dst = os.path.join(dirn, new_name)
        dst_final = next_nonconflicting_path(dst)
        if dst_final != dst:
            # collision will be resolved; keep dst_final as target
            pass
        changes.append((path, dst_final, is_dir))
    return changes


def print_progress(found: int, renamed: int):
    print(f"Progress: found {found} / renamed {renamed}", end="\r", flush=True)


def write_log_line(log_path: Optional[str], line: str):
    if not log_path:
        return
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(line.rstrip("\n") + "\n")
    except Exception:
        pass


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)

    # Determine mode and gather inputs
    case_sensitive = bool(args.cs)
    include_dirs = bool(args.include_dirs)
    dry_run = bool(args.dry_run)
    backup = bool(args.backup)
    json_log = bool(args.json_log)
    regex_mode = bool(getattr(args, "regex", False))
    find_only = bool(getattr(args, "find_only", False))
    exts = normalize_exts(args.ext)

    location = args.location
    find_term = args.find
    replace_term = args.replace if args.replace is not None else ""

    # Special CLI partials: if only find provided (no location), prompt for location and maybe replace
    if location is None and find_term is not None:
        print("Location not provided; switching to prompts for missing values.")
        prompted_location, prompted_find, prompted_replace = gather_inputs_interactive({
            "location": None,
            "find": find_term,
            "replace": replace_term,
            "cs": case_sensitive,
            "include_dirs": include_dirs,
            "dry_run": dry_run,
            "exts": exts,
            "backup": backup,
            "json_log": json_log,
            "regex": regex_mode,
        })
        location = prompted_location or location
        find_term = prompted_find or find_term
        replace_term = prompted_replace if prompted_replace is not None else replace_term

    # Fully interactive if no positionals
    if location is None and find_term is None:
        location, find_term, replace_term = gather_inputs_interactive({
            "cs": case_sensitive,
            "include_dirs": include_dirs,
            "dry_run": dry_run,
            "exts": exts,
            "backup": backup,
            "json_log": json_log,
        })

    # Validate
    if not location:
        print("Error: A location (drive or folder) is required.")
        return 2
    if not find_term:
        print("Error: A find term is required.")
        return 2

    location = os.path.abspath(location)
    if not os.path.exists(location):
        print(f"Error: Path does not exist: {location}")
        return 2

    # Show plan and ask for confirmation if we haven't already via interactive confirm
    if find_only:
        print("\nPlan:")
        print(f"  Location       : {location}")
        print(f"  Find term      : {find_term!r}")
        print(f"  Replace with   : (ignored in --find-only)")
        print(f"  Case-sensitive : {'Yes' if case_sensitive else 'No'}")
        print(f"  Regex mode     : {'Yes' if regex_mode else 'No'}")
        print(f"  Include dirs   : {'Yes' if include_dirs else 'No'}")
        print(f"  Dry-run        : {'Yes' if dry_run else 'No'}")
        print(f"  Backup copies  : {'Yes' if backup else 'No'}")
        print(f"  JSON log       : {'Yes' if json_log else 'No'}")
        print(f"  Extensions     : {'(all)' if not exts else ','.join(exts)}")
    else:
        ans = confirm_plan(location, find_term, replace_term, case_sensitive, include_dirs, dry_run, exts, backup, json_log, regex_mode)
        if ans in {"n", "no"}:
            print("Aborted by user.")
            return 0
    approve_each = ans == "a" if not find_only else False
    if not find_only and ans == "c":
        location, find_term, replace_term = gather_inputs_interactive({
            "location": location,
            "find": find_term,
            "replace": replace_term,
            "cs": case_sensitive,
            "include_dirs": include_dirs,
            "dry_run": dry_run,
            "exts": exts,
            "backup": backup,
            "json_log": json_log,
            "regex": regex_mode,
        })

    # Prepare logging (for both find-only and normal flows)
    log_path = ensure_log_file(os.getcwd()) if args.v else None
    json_log_path = ensure_json_log_file(os.getcwd()) if json_log else None
    if args.v:
        if log_path:
            print(f"Logging to: {log_path}")
        else:
            print("Warning: Could not create log file; continuing without file logging.")
    if json_log:
        if json_log_path:
            print(f"JSON log to: {json_log_path}")
        else:
            print("Warning: Could not create JSON log file; continuing without JSON logging.")

    # Plan changes
    print("\nScanning...")
    # Validate regex early to provide clear error if invalid
    if regex_mode:
        try:
            re.compile(find_term, 0 if case_sensitive else re.IGNORECASE)
        except re.error as e:
            print(f"Error: Invalid regex pattern: {e}")
            return 2
    if find_only:
        # Find-only mode
        matches = find_matches(location, find_term, case_sensitive, include_dirs, exts, regex_mode)
        total_found = len(matches)
        print(f"Found {total_found} item(s) matching.")
        renamed = 0
        skipped = 0
        errors = 0
        # Log each match
        for path, is_dir in matches:
            write_log_line(log_path, f"FIND-ONLY: {path}")
            write_json_log(json_log_path, {
                "ts": dt.datetime.utcnow().isoformat() + "Z",
                "action": "find",
                "src": path,
                "is_dir": is_dir,
                "status": "ok",
                "case_sensitive": case_sensitive,
                "include_dirs": include_dirs,
                "dry_run": dry_run,
                "backup": backup,
                "regex": regex_mode,
                "exts": exts,
            })
        # Summary
        print("\nJob Completed.")
        print(f"  Total found : {total_found}")
        print(f"  Renamed     : {renamed}")
        print(f"  Skipped     : {skipped}")
        print(f"  Errors      : {errors}")
        write_json_log(json_log_path, {
            "ts": dt.datetime.utcnow().isoformat() + "Z",
            "action": "summary",
            "total_found": total_found,
            "renamed": renamed,
            "skipped": skipped,
            "errors": errors,
            "case_sensitive": case_sensitive,
            "include_dirs": include_dirs,
            "dry_run": dry_run,
            "backup": backup,
            "regex": regex_mode,
            "exts": exts,
        })
        if json_log_path:
            print(f"JSON log written to: {json_log_path}")
        return 0
    # Normal rename planning
    changes = plan_changes(location, find_term, replace_term, case_sensitive, include_dirs, exts, regex_mode)
    total_found = len(changes)
    print(f"Found {total_found} item(s) to rename.")

    if total_found == 0:
        print("Nothing to do.")
        return 0

    # If user chose 'a' approve-each, confirm each change
    to_apply: List[Tuple[str, str, bool]] = []
    if approve_each:
        for idx, (src, dst, is_dir) in enumerate(changes, 1):
            rel = os.path.relpath(src, start=location)
            print(f"[{idx}/{total_found}] {rel}")
            print(f"  -> {os.path.basename(dst)}")
            while True:
                resp = input("Rename this item? [y/n/q]: ").strip().lower()
                if resp in {"y", "yes"}:
                    to_apply.append((src, dst, is_dir))
                    break
                elif resp in {"n", "no"}:
                    break
                elif resp in {"q"}:
                    print("Stopping approvals early.")
                    # Append nothing further
                    break
                else:
                    print("Please answer y, n, or q.")
            print()
    else:
        to_apply = changes

    # Execute
    renamed = 0
    skipped = 0
    errors = 0
    print()
    for src, dst, is_dir in to_apply:
        print_progress(total_found, renamed)
        if dry_run:
            if backup and not is_dir:
                bk = backup_nonconflicting_path(src)
                write_log_line(log_path, f"DRY-RUN BACKUP: {src} -> {bk}")
                write_json_log(json_log_path, {
                    "ts": dt.datetime.utcnow().isoformat() + "Z",
                    "action": "dry_run_backup",
                    "src": src,
                    "dst": bk,
                    "is_dir": is_dir,
                    "status": "ok",
                    "case_sensitive": case_sensitive,
                    "include_dirs": include_dirs,
                    "dry_run": True,
                    "backup": backup,
                    "regex": regex_mode,
                    "exts": exts,
                })
            write_log_line(log_path, f"DRY-RUN: {src} -> {dst}")
            write_json_log(json_log_path, {
                "ts": dt.datetime.utcnow().isoformat() + "Z",
                "action": "dry_run_rename",
                "src": src,
                "dst": dst,
                "is_dir": is_dir,
                "status": "ok",
                "case_sensitive": case_sensitive,
                "include_dirs": include_dirs,
                "dry_run": True,
                "backup": backup,
                "regex": regex_mode,
                "exts": exts,
            })
            renamed += 1  # count as processed for progress purposes
            continue
        try:
            # Backup (files only)
            if backup and not is_dir:
                bk_path = backup_nonconflicting_path(src)
                try:
                    shutil.copy2(src, bk_path)
                    write_log_line(log_path, f"BACKUP: {src} -> {bk_path}")
                    write_json_log(json_log_path, {
                        "ts": dt.datetime.utcnow().isoformat() + "Z",
                        "action": "backup",
                        "src": src,
                        "dst": bk_path,
                        "is_dir": is_dir,
                        "status": "ok",
                        "case_sensitive": case_sensitive,
                        "include_dirs": include_dirs,
                        "dry_run": False,
                        "backup": backup,
                        "regex": regex_mode,
                        "exts": exts,
                    })
                except Exception as e:
                    write_log_line(log_path, f"ERROR (backup failed): {src} -> {bk_path} :: {e}")
                    write_json_log(json_log_path, {
                        "ts": dt.datetime.utcnow().isoformat() + "Z",
                        "action": "backup",
                        "src": src,
                        "dst": bk_path,
                        "is_dir": is_dir,
                        "status": "failed",
                        "error": str(e),
                        "case_sensitive": case_sensitive,
                        "include_dirs": include_dirs,
                        "dry_run": False,
                        "backup": backup,
                        "regex": regex_mode,
                        "exts": exts,
                    })
                    errors += 1
                    continue
            os.rename(src, dst)
            write_log_line(log_path, f"RENAMED: {src} -> {dst}")
            write_json_log(json_log_path, {
                "ts": dt.datetime.utcnow().isoformat() + "Z",
                "action": "rename",
                "src": src,
                "dst": dst,
                "is_dir": is_dir,
                "status": "ok",
                "case_sensitive": case_sensitive,
                "include_dirs": include_dirs,
                "dry_run": False,
                "backup": backup,
                "regex": regex_mode,
                "exts": exts,
            })
            renamed += 1
        except FileNotFoundError:
            write_log_line(log_path, f"ERROR (not found): {src}")
            write_json_log(json_log_path, {
                "ts": dt.datetime.utcnow().isoformat() + "Z",
                "action": "rename",
                "src": src,
                "dst": dst,
                "is_dir": is_dir,
                "status": "failed",
                "error": "FileNotFoundError",
                "case_sensitive": case_sensitive,
                "include_dirs": include_dirs,
                "dry_run": False,
                "backup": backup,
                "regex": regex_mode,
                "exts": exts,
            })
            errors += 1
        except PermissionError:
            write_log_line(log_path, f"ERROR (permission): {src}")
            write_json_log(json_log_path, {
                "ts": dt.datetime.utcnow().isoformat() + "Z",
                "action": "rename",
                "src": src,
                "dst": dst,
                "is_dir": is_dir,
                "status": "failed",
                "error": "PermissionError",
                "case_sensitive": case_sensitive,
                "include_dirs": include_dirs,
                "dry_run": False,
                "backup": backup,
                "regex": regex_mode,
                "exts": exts,
            })
            errors += 1
        except Exception as e:
            write_log_line(log_path, f"ERROR: {src} -> {dst} :: {e}")
            write_json_log(json_log_path, {
                "ts": dt.datetime.utcnow().isoformat() + "Z",
                "action": "rename",
                "src": src,
                "dst": dst,
                "is_dir": is_dir,
                "status": "failed",
                "error": str(e),
                "case_sensitive": case_sensitive,
                "include_dirs": include_dirs,
                "dry_run": False,
                "backup": backup,
                "regex": regex_mode,
                "exts": exts,
            })
            errors += 1

    # Final progress line cleanup
    print_progress(total_found, renamed)
    print()

    # Summary
    print("Job Completed.")
    print(f"  Total found : {total_found}")
    print(f"  Renamed     : {renamed}")
    if approve_each:
        skipped = total_found - renamed - errors
    print(f"  Skipped     : {skipped}")
    print(f"  Errors      : {errors}")
    if args.v and log_path:
        print(f"Detailed log written to: {log_path}")
    if json_log and json_log_path:
        # write a final summary JSON log line
        write_json_log(json_log_path, {
            "ts": dt.datetime.utcnow().isoformat() + "Z",
            "action": "summary",
            "total_found": total_found,
            "renamed": renamed,
            "skipped": skipped,
            "errors": errors,
            "case_sensitive": case_sensitive,
            "include_dirs": include_dirs,
            "dry_run": dry_run,
            "backup": backup,
            "regex": regex_mode,
            "exts": exts,
        })
        print(f"JSON log written to: {json_log_path}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)

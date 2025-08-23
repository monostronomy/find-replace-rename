# Demo script for --find-only mode
# Usage: Run from repo root: powershell -ExecutionPolicy Bypass -File scripts/demo_findonly.ps1

param(
    [string]$Root = (Split-Path -Parent $MyInvocation.MyCommand.Path)
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Move to repo root if invoked from elsewhere
$repo = Split-Path -Parent $Root
Push-Location $repo
try {
    $td = 'demo_findonly'
    if (Test-Path $td) { Remove-Item -Recurse -Force $td }
    New-Item -ItemType Directory -Path $td | Out-Null

    # Files and dirs
    New-Item -ItemType File -Path (Join-Path $td 'Report-123.txt') | Out-Null
    New-Item -ItemType File -Path (Join-Path $td 'Report-456.pdf') | Out-Null
    New-Item -ItemType File -Path (Join-Path $td 'draft_note.txt') | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $td 'Reports') | Out-Null
    New-Item -ItemType File -Path (Join-Path $td 'Reports/Report-789.txt') | Out-Null

    Write-Host "\n== Literal search with JSONL ==" -ForegroundColor Cyan
    python file_renamer.py --find-only --json-log $td 'Report'

    Write-Host "\n== Regex search (Report-(\\d+)) ==" -ForegroundColor Cyan
    python file_renamer.py --find-only --regex $td 'Report-(\d+)'

    Write-Host "\n== Regex + include-dirs + .txt filter ==" -ForegroundColor Cyan
    python file_renamer.py --find-only --regex --include-dirs --ext '.txt' $td '(?i)report'
}
finally {
    Pop-Location
}

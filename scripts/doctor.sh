#!/usr/bin/env bash
set -u

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
workbench_root=$(CDPATH= cd -- "$script_dir/.." && pwd -P)

pass() { printf '[PASS] %s\n' "$1"; }
warn() { printf '[WARN] %s\n' "$1"; }
info() { printf '[INFO] %s\n' "$1"; }

printf 'Math Research Workbench doctor\n'
if [ -f "$workbench_root/VERSION" ]; then
  info "Workbench version: v$(sed -n '1p' "$workbench_root/VERSION")"
fi
info "Workspace location inspected (path hidden)."

sync_path=false
case "$workbench_root/" in
  *"/Library/CloudStorage/"*|*"/Library/Mobile Documents/"*|*"/OneDrive/"*|*"/OneDrive - "*|*"/OneDrive-"*|*"/Dropbox/"*|*"/Dropbox ("*|*" Dropbox/"*|*"/Google Drive/"*|*"/GoogleDrive/"*|*"/iCloudDrive/"*)
    sync_path=true
    ;;
esac

if [ -n "${HOME:-}" ]; then
  case "$workbench_root" in
    "$HOME/Desktop"|"$HOME/Desktop/"*|"$HOME/Documents"|"$HOME/Documents/"*)
      warn "Workspace is under Desktop or Documents, which may be cloud-synced. Verify the location before setup."
      ;;
  esac
fi

if [ "$sync_path" = true ]; then
  warn "Workspace appears to be inside a cloud-sync folder. Move it to a local non-sync folder while Codex and Obsidian are closed."
else
  pass "No common cloud-sync folder name was detected in the workspace path."
fi

if command -v git >/dev/null 2>&1; then
  pass "Git is available."
  if git -C "$workbench_root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    pass "This folder is a Git working tree."
  else
    info "This folder is not a Git working tree; GitHub backup is optional."
  fi
  if git config --global --get user.name >/dev/null 2>&1 && git config --global --get user.email >/dev/null 2>&1; then
    pass "Git author identity is configured."
  else
    info "Git author identity is not fully configured. It is needed only if Git backup is enabled."
  fi
else
  info "Git is not installed. The workbench still works without GitHub backup."
fi

if command -v gh >/dev/null 2>&1; then
  pass "GitHub CLI is available."
  if gh auth status >/dev/null 2>&1; then
    pass "GitHub CLI has an authenticated account."
  else
    info "GitHub CLI is not authenticated. Use browser/device login only if GitHub backup is selected."
  fi
else
  info "GitHub CLI is not installed; GitHub backup can be configured later."
fi

if command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1; then
  pass "Python is available for redacted setup diagnostics."
else
  info "Python was not detected. Markdown still works; remote visibility must be treated as unknown unless GitHub CLI can verify it."
fi

if command -v obsidian >/dev/null 2>&1 || [ -d /Applications/Obsidian.app ] || [ -d "${HOME:-}/Applications/Obsidian.app" ]; then
  pass "Obsidian appears to be installed."
else
  info "Obsidian was not detected; it is optional."
fi

if command -v latexmk >/dev/null 2>&1; then
  pass "latexmk is available for local TeX compilation."
else
  info "latexmk was not detected; use Overleaf or configure local TeX later."
fi

if [ -f "$workbench_root/.harness/local.yaml" ]; then
  if grep -Eq '^status:[[:space:]]*complete[[:space:]]*$' "$workbench_root/.harness/local.yaml"; then
    if grep -Eq '^setup_version:[[:space:]]*1[[:space:]]*$' "$workbench_root/.harness/local.yaml"; then
      pass "First-run setup is marked complete for setup version 1."
    else
      warn "First-run setup is complete but its setup version is missing or outdated. Run setup again."
    fi
  else
    info "First-run setup has saved progress but is not marked complete."
  fi
else
  info "First-run setup has not created local state yet."
fi

printf 'Doctor finished. WARN items need attention; INFO items are optional.\n'

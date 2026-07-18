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

if command -v claude >/dev/null 2>&1; then
  pass "Claude Code is available."
  info "Claude login readiness is checked privately only after Claude review is selected."
else
  info "Claude Code was not detected; Claude review is optional."
fi

info "ChatGPT Browser sign-in is not inferred by this shell check; verify it inside Codex's in-app Browser only when selected."

python_command=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 &&
     "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
    python_command=$candidate
    break
  fi
done
if [ -n "$python_command" ]; then
  pass "Python 3.9 or newer is available for redacted setup diagnostics."
else
  warn "Python 3.9 or newer was not detected. Markdown still works, but safe saved first-run setup and resume require a compatible bundled workspace runtime or an approved official Python installation."
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

local_state="$workbench_root/.harness/local.yaml"
if [ -n "$python_command" ]; then
  state_output=$("$python_command" "$workbench_root/scripts/setup-state.py" 2>/dev/null)
  state_exit=$?
  setup_state=$(printf '%s\n' "$state_output" | sed -n 's/^setup_state=//p' | sed -n '1p')
  setup_status=$(printf '%s\n' "$state_output" | sed -n 's/^status=//p' | sed -n '1p')
  case "$setup_state" in
    missing)
      info "First-run setup has not created local state yet."
      ;;
    ok)
      if [ "$setup_status" = "complete" ]; then
        pass "First-run setup is marked complete for setup version 2."
      else
        info "First-run setup has saved progress but is not marked complete."
      fi
      ;;
    outdated)
      if [ "$setup_status" = "complete" ]; then
        info "An optional first-run update is available. Existing version 1 answers remain usable; after any required private-remote safety check, setup can ask the two new questions."
      else
        info "Version 1 setup has saved progress. Resume its remaining original questions first, then answer the two new questions."
      fi
      ;;
    unsupported)
      warn "The local setup was written by a newer unsupported setup version. Do not resume or write it; update the workbench first."
      ;;
    inconsistent)
      warn "The saved first-run setup is internally inconsistent. Do not write it automatically; use the setup recovery guide."
      ;;
    invalid|unreadable)
      warn "The saved first-run setup could not be read safely. Do not resume or write it; use the setup recovery guide."
      ;;
    *)
      if [ "$state_exit" -ne 0 ]; then
        warn "The redacted first-run state check failed. Do not resume or write setup state; use the recovery guide."
      else
        warn "First-run setup state could not be classified. Do not resume or write setup state; use the recovery guide."
      fi
      ;;
  esac
else
  if [ -L "$workbench_root/.harness" ] || [ -L "$local_state" ]; then
    warn "First-run state uses an unsafe link. Do not resume or write it; use the setup recovery guide."
  elif [ -f "$local_state" ]; then
    info "First-run state was found but cannot be inspected safely without Python. Do not change it automatically."
  else
    info "First-run setup has not created local state yet."
  fi
fi

printf 'Doctor finished. WARN items need attention; INFO items are optional.\n'

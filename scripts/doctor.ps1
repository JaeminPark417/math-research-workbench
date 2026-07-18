[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)

$WorkBenchRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Write-Pass([string]$Message) { Write-Host "[PASS] $Message" }
function Write-Warn([string]$Message) { Write-Host "[WARN] $Message" }
function Write-Info([string]$Message) { Write-Host "[INFO] $Message" }

Write-Host "Math Research Workbench doctor"
$VersionFile = Join-Path $WorkBenchRoot "VERSION"
if (Test-Path -LiteralPath $VersionFile -PathType Leaf) {
    $WorkbenchVersion = (Get-Content -LiteralPath $VersionFile -TotalCount 1).Trim()
    Write-Info "Workbench version: v$WorkbenchVersion"
}
Write-Info "Workspace location inspected (path hidden)."

$SyncPattern = '(?i)([\\/](OneDrive(?: - [^\\/]+)?|Dropbox(?: \([^\\/]+\))?|[^\\/]+ Dropbox|Google Drive|GoogleDrive|iCloud(?:Drive)?|CloudStorage)[\\/])'
$KnownSyncRoots = @(
    @(
        $env:OneDrive,
        $env:OneDriveCommercial,
        $env:OneDriveConsumer
    ) | Where-Object { $_ }
)
$DropboxInfoFiles = @(
    if ($env:APPDATA) { Join-Path $env:APPDATA "Dropbox\info.json" }
    if ($env:LOCALAPPDATA) { Join-Path $env:LOCALAPPDATA "Dropbox\info.json" }
) | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) }
foreach ($InfoFile in $DropboxInfoFiles) {
    try {
        $DropboxInfo = Get-Content -LiteralPath $InfoFile -Raw | ConvertFrom-Json
        foreach ($Account in $DropboxInfo.PSObject.Properties.Value) {
            if ($Account.path) { $KnownSyncRoots += [string]$Account.path }
        }
    } catch {
        # A malformed provider file is not printed because it may contain paths.
    }
}
$UnderKnownSyncRoot = $false
foreach ($Root in $KnownSyncRoots) {
    try {
        $NormalizedRoot = [System.IO.Path]::GetFullPath($Root).TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
        $NormalizedWorkBench = $WorkBenchRoot.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
        if ($NormalizedWorkBench.StartsWith($NormalizedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            $UnderKnownSyncRoot = $true
            break
        }
    } catch {
        # Ignore an invalid provider environment variable and continue safely.
    }
}
$WorkBenchDrive = [System.IO.Path]::GetPathRoot($WorkBenchRoot).TrimEnd('\', '/')
$SystemDrive = if ($env:SystemDrive) { $env:SystemDrive.TrimEnd('\', '/') } else { "" }
$NonSystemDrive = $SystemDrive -and -not $WorkBenchDrive.Equals($SystemDrive, [System.StringComparison]::OrdinalIgnoreCase)

if (($WorkBenchRoot -match $SyncPattern) -or $UnderKnownSyncRoot) {
    Write-Warn "Workspace appears to be inside a cloud-sync folder. Move it while Codex and Obsidian are closed."
} elseif ($env:USERPROFILE -and (($WorkBenchRoot -like "$env:USERPROFILE\Desktop\*") -or ($WorkBenchRoot -like "$env:USERPROFILE\Documents\*"))) {
    Write-Warn "Workspace is under Desktop or Documents, which may be redirected to OneDrive. Verify the location."
} elseif ($NonSystemDrive) {
    Write-Warn "Workspace is on a non-system drive, which may be removable or cloud-mounted. Verify that it is a local non-sync location."
} else {
    Write-Pass "No common cloud-sync folder name was detected in the workspace path."
}

$Git = Get-Command git -ErrorAction SilentlyContinue
if ($Git) {
    Write-Pass "Git is available."
    & git -C $WorkBenchRoot rev-parse --is-inside-work-tree *> $null
    if ($LASTEXITCODE -eq 0) { Write-Pass "This folder is a Git working tree." }
    else { Write-Info "This folder is not a Git working tree; GitHub backup is optional." }

    & git config --global --get user.name *> $null
    $NameConfigured = $LASTEXITCODE -eq 0
    & git config --global --get user.email *> $null
    $EmailConfigured = $LASTEXITCODE -eq 0
    if ($NameConfigured -and $EmailConfigured) { Write-Pass "Git author identity is configured." }
    else { Write-Info "Git author identity is not fully configured. It is needed only for Git backup." }
} else {
    Write-Info "Git is not installed. The workbench still works without GitHub backup."
}

$Gh = Get-Command gh -ErrorAction SilentlyContinue
if ($Gh) {
    Write-Pass "GitHub CLI is available."
    & gh auth status *> $null
    if ($LASTEXITCODE -eq 0) { Write-Pass "GitHub CLI has an authenticated account." }
    else { Write-Info "GitHub CLI is not authenticated. Browser/device login is used only if selected." }
} else {
    Write-Info "GitHub CLI is not installed; GitHub backup can be configured later."
}

$Claude = Get-Command claude -ErrorAction SilentlyContinue
if ($Claude) {
    Write-Pass "Claude Code is available."
    Write-Info "Claude login readiness is checked privately only after Claude review is selected."
} else {
    Write-Info "Claude Code was not detected; Claude review is optional."
}

Write-Info "ChatGPT Browser sign-in is not inferred by this shell check; verify it inside Codex's in-app Browser only when selected."

$PythonCommand = $null
$PythonPrefixArgs = @()
foreach ($PythonName in @("python3", "python", "py")) {
    $Candidate = Get-Command $PythonName -ErrorAction SilentlyContinue
    if (-not $Candidate) { continue }
    $CandidatePrefixArgs = if ($PythonName -eq "py") { @("-3") } else { @() }
    & $Candidate.Source @CandidatePrefixArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" *> $null
    if ($LASTEXITCODE -eq 0) {
        $PythonCommand = $Candidate
        $PythonPrefixArgs = $CandidatePrefixArgs
        break
    }
}
if ($PythonCommand) {
    Write-Pass "Python 3.9 or newer is available for redacted setup diagnostics."
} else {
    Write-Warn "Python 3.9 or newer was not detected. Markdown still works, but safe saved first-run setup and resume require a compatible bundled workspace runtime or an approved official Python installation."
}

$ObsidianCandidates = @()
if ($env:LOCALAPPDATA) {
    $ObsidianCandidates += Join-Path $env:LOCALAPPDATA "Obsidian\Obsidian.exe"
}
if ($env:ProgramFiles) {
    $ObsidianCandidates += Join-Path $env:ProgramFiles "Obsidian\Obsidian.exe"
}
$ObsidianCommand = Get-Command obsidian -ErrorAction SilentlyContinue
if ($ObsidianCommand -or ($ObsidianCandidates | Where-Object { $_ -and (Test-Path $_) })) {
    Write-Pass "Obsidian appears to be installed."
} else {
    Write-Info "Obsidian was not detected; it is optional."
}

if (Get-Command latexmk -ErrorAction SilentlyContinue) {
    Write-Pass "latexmk is available for local TeX compilation."
} else {
    Write-Info "latexmk was not detected; use Overleaf or configure local TeX later."
}

$LocalState = Join-Path $WorkBenchRoot ".harness\local.yaml"
if ($PythonCommand) {
    $SetupStateScript = Join-Path $WorkBenchRoot "scripts\setup-state.py"
    $StateOutput = @(& $PythonCommand.Source @PythonPrefixArgs $SetupStateScript 2>$null)
    $StateExit = $LASTEXITCODE
    $SetupStateLine = $StateOutput | Where-Object { $_ -like "setup_state=*" } | Select-Object -First 1
    $SetupStatusLine = $StateOutput | Where-Object { $_ -like "status=*" } | Select-Object -First 1
    $SetupState = if ($SetupStateLine) { $SetupStateLine.Substring("setup_state=".Length) } else { "" }
    $SetupStatus = if ($SetupStatusLine) { $SetupStatusLine.Substring("status=".Length) } else { "" }
    switch ($SetupState) {
        "missing" {
            Write-Info "First-run setup has not created local state yet."
        }
        "ok" {
            if ($SetupStatus -eq "complete") {
                Write-Pass "First-run setup is marked complete for setup version 2."
            } else {
                Write-Info "First-run setup has saved progress but is not marked complete."
            }
        }
        "outdated" {
            if ($SetupStatus -eq "complete") {
                Write-Info "An optional first-run update is available. Existing version 1 answers remain usable; after any required private-remote safety check, setup can ask the two new questions."
            } else {
                Write-Info "Version 1 setup has saved progress. Resume its remaining original questions first, then answer the two new questions."
            }
        }
        "unsupported" {
            Write-Warn "The local setup was written by a newer unsupported setup version. Do not resume or write it; update the workbench first."
        }
        "inconsistent" {
            Write-Warn "The saved first-run setup is internally inconsistent. Do not write it automatically; use the setup recovery guide."
        }
        { $_ -in @("invalid", "unreadable") } {
            Write-Warn "The saved first-run setup could not be read safely. Do not resume or write it; use the setup recovery guide."
        }
        default {
            if ($StateExit -ne 0) {
                Write-Warn "The redacted first-run state check failed. Do not resume or write setup state; use the recovery guide."
            } else {
                Write-Warn "First-run setup state could not be classified. Do not resume or write setup state; use the recovery guide."
            }
        }
    }
} else {
    $HarnessItem = Get-Item -LiteralPath (Join-Path $WorkBenchRoot ".harness") -Force -ErrorAction SilentlyContinue
    $StateItem = Get-Item -LiteralPath $LocalState -Force -ErrorAction SilentlyContinue
    $UnsafeStateLink =
        ($HarnessItem -and ($HarnessItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) -or
        ($StateItem -and ($StateItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint))
    if ($UnsafeStateLink) {
        Write-Warn "First-run state uses an unsafe link or junction. Do not resume or write it; use the setup recovery guide."
    } elseif ($StateItem) {
        Write-Info "First-run state was found but cannot be inspected safely without Python. Do not change it automatically."
    } else {
        Write-Info "First-run setup has not created local state yet."
    }
}

Write-Host "Doctor finished. WARN items need attention; INFO items are optional."

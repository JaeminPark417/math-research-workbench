[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Source,

    [Parameter(Position = 1)]
    [ValidateSet("pdflatex", "xelatex", "lualatex")]
    [string]$Engine = "pdflatex"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)

function Assert-NoReparsePointInPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Candidate,

        [Parameter(Mandatory = $true)]
        [string]$Root
    )

    $RootFull = [System.IO.Path]::GetFullPath($Root)
    $RootPrefix = $RootFull.TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    ) + [System.IO.Path]::DirectorySeparatorChar
    $CandidateFull = [System.IO.Path]::GetFullPath($Candidate)
    if (-not $CandidateFull.StartsWith($RootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path resolved outside this workbench."
    }

    $RootItem = Get-Item -LiteralPath $RootFull
    if ($RootItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
        throw "Workbench path must not be a symbolic link or junction."
    }

    $Current = $RootFull
    $Relative = $CandidateFull.Substring($RootPrefix.Length)
    foreach ($Component in ($Relative -split '[\\/]')) {
        if (-not $Component) { continue }
        $Current = Join-Path $Current $Component
        if (-not (Test-Path -LiteralPath $Current)) { break }
        $Item = Get-Item -LiteralPath $Current
        if ($Item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
            throw "Path must not contain a symbolic link or junction."
        }
    }
}

if (-not (Get-Command latexmk -ErrorAction SilentlyContinue)) {
    throw "latexmk was not found. Choose Overleaf or run first-run TeX setup."
}

if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
    throw "The selected TeX source was not found."
}
$SourceItem = Get-Item -LiteralPath $Source
if ($SourceItem.LinkType) {
    throw "TeX source must not be a symbolic link."
}
$SourcePath = $SourceItem.FullName
if ([System.IO.Path]::GetExtension($SourcePath) -ne ".tex") {
    throw "Expected a source file whose name ends in .tex."
}

$WorkBenchRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RootPrefix = $WorkBenchRoot.TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
if (-not $SourcePath.StartsWith($RootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "TeX source must be inside this workbench."
}
Assert-NoReparsePointInPath -Candidate $SourcePath -Root $WorkBenchRoot

$RelativeSource = $SourcePath.Substring($RootPrefix.Length)
$RelativeDirectory = [System.IO.Path]::GetDirectoryName($RelativeSource)
$Stem = [System.IO.Path]::GetFileNameWithoutExtension($SourcePath)
$BuildRoot = Join-Path $WorkBenchRoot "build"
if ($RelativeDirectory) {
    $BuildRoot = Join-Path $BuildRoot $RelativeDirectory
}
$BuildDirectory = Join-Path $BuildRoot $Stem
Assert-NoReparsePointInPath -Candidate $BuildDirectory -Root $WorkBenchRoot
[System.IO.Directory]::CreateDirectory($BuildDirectory) | Out-Null
Assert-NoReparsePointInPath -Candidate $BuildDirectory -Root $WorkBenchRoot
$BuildDirectory = [System.IO.Path]::GetFullPath($BuildDirectory)

$EngineFlag = switch ($Engine) {
    "pdflatex" { "-pdf" }
    "xelatex" { "-xelatex" }
    "lualatex" { "-lualatex" }
}

$LatexArguments = @(
    "-norc",
    "-cd",
    $EngineFlag,
    "-no-shell-escape",
    "-halt-on-error",
    "-interaction=nonstopmode",
    "-outdir=$BuildDirectory",
    $SourcePath
)

& latexmk @LatexArguments
if ($LASTEXITCODE -ne 0) {
    throw "TeX compilation failed with exit code $LASTEXITCODE."
}

$PdfPath = Join-Path $BuildDirectory "$Stem.pdf"
if (-not (Test-Path -LiteralPath $PdfPath -PathType Leaf)) {
    throw "TeX command finished without producing the expected PDF."
}
$RelativePdfPath = $PdfPath.Substring($RootPrefix.Length)
Write-Host "Compiled PDF: $RelativePdfPath"

# Local TeX reference

Local TeX is optional. Obsidian can display math without it, and Overleaf can
compile manuscripts in a browser. Recommend `later` or Overleaf to a beginner
unless offline or local compilation is important.

## Preflight

Check read-only:

```text
latexmk --version
pdflatex --version
xelatex --version
lualatex --version
```

If `latexmk` and one PDF engine work, do not reinstall TeX.

## Installation policy

Use the current official distribution or the operating system's established
package manager. Before installing:

1. identify the OS and architecture;
2. show the package/distribution name and official source;
3. use the package manager to report download or disk impact when possible; on
   Homebrew, set `HOMEBREW_NO_AUTO_UPDATE=1` for information-only checks so a
   size lookup does not trigger an automatic update;
4. show the exact command and whether administrator permission is required;
5. obtain explicit approval.

Useful official starting points:

- TeX Live: <https://tug.org/texlive/>
- MacTeX and BasicTeX: <https://tug.org/mactex/>
- MiKTeX: <https://miktex.org/download>
- Overleaf: <https://www.overleaf.com/>

Do not pipe an unreviewed remote installer into a shell. Do not install a full
multi-gigabyte distribution without describing that impact.

If the official source or package manager does not report a size, say
"size could not be determined". Do not invent an estimate. A command described
as read-only must not refresh package indexes or update package-manager state.

## Verification

Compile the included sample through the wrapper, not with an improvised command:

- macOS/Linux:
  `bash scripts/compile-tex.sh meta/templates/article.tex`
- Windows:
  `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/compile-tex.ps1 meta/templates/article.tex`

The default engine is `pdflatex`. If setup verified another engine, pass it
explicitly:

- macOS/Linux: `bash scripts/compile-tex.sh --engine xelatex path/to/file.tex`
- Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/compile-tex.ps1 -Source path/to/file.tex -Engine xelatex`

The wrapper must use `latexmk -norc`, halt on errors, and disable shell escape.
`-norc` prevents project or user `latexmk` startup files from changing the
wrapper's safety options. It must build from the source directory so relative
inputs work, while placing each source's output in a distinct ignored directory
under `build/`. Report the output path. A failed verification leaves setup
usable with `tex.choice: "later"`; explain the failed verification separately
instead of inventing another state value.

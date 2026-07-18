#!/usr/bin/env bash
set -euo pipefail

engine=pdflatex
if [ "$#" -eq 1 ]; then
  source_input=$1
elif [ "$#" -eq 3 ] && [ "$1" = "--engine" ]; then
  engine=$2
  source_input=$3
else
  printf 'Usage: %s [--engine pdflatex|xelatex|lualatex] path/to/document.tex\n' "$0" >&2
  exit 2
fi

case "$engine" in
  pdflatex) engine_flag=-pdf ;;
  xelatex) engine_flag=-xelatex ;;
  lualatex) engine_flag=-lualatex ;;
  *) printf 'Unsupported TeX engine: %s\n' "$engine" >&2; exit 2 ;;
esac

if ! command -v latexmk >/dev/null 2>&1; then
  printf 'latexmk was not found. Choose Overleaf or run first-run TeX setup.\n' >&2
  exit 3
fi

if [ ! -f "$source_input" ]; then
  printf 'The selected TeX source was not found.\n' >&2
  exit 4
fi

case "$source_input" in
  *.tex) ;;
  *) printf 'Expected a source file whose name ends in .tex.\n' >&2; exit 5 ;;
esac

if [ -L "$source_input" ]; then
  printf 'TeX source must not be a symbolic link.\n' >&2
  exit 6
fi

source_dir=$(CDPATH= cd -- "$(dirname -- "$source_input")" && pwd -P)
source_name=$(basename -- "$source_input")
source_abs="$source_dir/$source_name"
stem=${source_name%.tex}
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
workbench_root=$(CDPATH= cd -- "$script_dir/.." && pwd -P)

case "$source_abs" in
  "$workbench_root"/*) relative_source=${source_abs#"$workbench_root"/} ;;
  *) printf 'TeX source must be inside this workbench.\n' >&2; exit 6 ;;
esac

relative_dir=$(dirname -- "$relative_source")
if [ "$relative_dir" = "." ]; then
  build_dir="$workbench_root/build/$stem"
  build_relative="build/$stem"
else
  build_dir="$workbench_root/build/$relative_dir/$stem"
  build_relative="build/$relative_dir/$stem"
fi

check_path=$workbench_root
remaining=$build_relative
while [ -n "$remaining" ]; do
  case "$remaining" in
    */*) component=${remaining%%/*}; remaining=${remaining#*/} ;;
    *) component=$remaining; remaining= ;;
  esac
  check_path="$check_path/$component"
  if [ -L "$check_path" ]; then
    printf 'Build path must not contain a symbolic link.\n' >&2
    exit 6
  fi
done

mkdir -p "$build_dir"
build_physical=$(CDPATH= cd -- "$build_dir" && pwd -P)
case "$build_physical" in
  "$workbench_root"/build/*) ;;
  *) printf 'Build directory resolved outside this workbench.\n' >&2; exit 6 ;;
esac
latexmk -norc -cd "$engine_flag" -no-shell-escape -halt-on-error -interaction=nonstopmode \
  -outdir="$build_physical" "$source_abs"

pdf_path="$build_physical/$stem.pdf"
if [ ! -f "$pdf_path" ]; then
  printf 'TeX command finished without producing the expected PDF.\n' >&2
  exit 7
fi
printf 'Compiled PDF: %s\n' "${pdf_path#"$workbench_root"/}"

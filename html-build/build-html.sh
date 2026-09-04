#!/usr/bin/env bash
set -euo pipefail

source_file="${1:-mdlayout.tex}"
output_file="${2:-mdlayout.html}"
style_file="${3:-}"
preamble_file="${4:-}"
script_dir="$(cd "$(dirname "$0")" && pwd)"
work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT

if [[ -z "$style_file" ]]; then
  source_dir="$(cd "$(dirname "$source_file")" && pwd)"
  if [[ -f "$source_dir/mdlayout.sty" ]]; then
    style_file="$source_dir/mdlayout.sty"
  else
    for candidate in "$source_dir"/mdlayout\(*\).sty; do
      [[ -f "$candidate" ]] && style_file="$candidate" && break
    done
  fi
fi

if [[ -z "$preamble_file" ]]; then
  source_dir="${source_dir:-$(cd "$(dirname "$source_file")" && pwd)}"
  [[ -f "$source_dir/mdpreamble.tex" ]] && preamble_file="$source_dir/mdpreamble.tex"
fi

preprocess_args=("$source_file" "$work_dir/mdlayout-prepared.tex" "$work_dir/mdlayout-html-data.json")
[[ -n "$style_file" ]] && preprocess_args+=(--style "$style_file")
[[ -n "$preamble_file" ]] && preprocess_args+=(--preamble "$preamble_file")
python3 "$script_dir/mdlayout-preprocess.py" "${preprocess_args[@]}"

MDLAYOUT_HTML_DATA="$work_dir/mdlayout-html-data.json" pandoc \
  "$work_dir/mdlayout-prepared.tex" \
  --from=latex+raw_tex --to=html5 --standalone --number-sections \
  --mathjax="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml-full.js" \
  --lua-filter="$script_dir/mdlayout.lua" --lua-filter="$script_dir/mdlayout.lua" \
  --lua-filter="$script_dir/mdlayout.lua" --lua-filter="$script_dir/mdlayout.lua" \
  --css="mdlayout.css" \
  --metadata pagetitle="mdlayout — User's Guide" \
  --output="$output_file"

python3 "$script_dir/mdlayout-postprocess.py" "$output_file" "$source_file"
python3 "$script_dir/embed-web-assets.py" "$output_file" "$script_dir/mdlayout.css"

echo "Created $output_file"

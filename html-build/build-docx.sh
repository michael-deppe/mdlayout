#!/usr/bin/env bash
set -euo pipefail

source_file="${1:-mdlayout.tex}"
output_file="${2:-mdlayout.docx}"
style_file="${3:-}"
preamble_file="${4:-}"
reference_doc="${5:-}"
script_dir="$(cd "$(dirname "$0")" && pwd)"
source_dir="$(cd "$(dirname "$source_file")" && pwd)"
work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT

# Keep the short invocation useful: project-local support files are picked up
# automatically, while explicit arguments continue to take precedence.
if [[ -z "$style_file" && -f "$source_dir/mdlayout.sty" ]]; then
  style_file="$source_dir/mdlayout.sty"
fi
if [[ -z "$preamble_file" && -f "$source_dir/mdpreamble.tex" ]]; then
  preamble_file="$source_dir/mdpreamble.tex"
fi

"$script_dir/build-html.sh" \
  "$source_file" "$work_dir/mdlayout.html" "$style_file" "$preamble_file"

python3 "$script_dir/prepare-docx-html.py" \
  "$work_dir/mdlayout.html" "$work_dir/mdlayout-docx.html"

pandoc_args=(
  "$work_dir/mdlayout-docx.html"
  --from=html+tex_math_single_backslash
  --to=docx
  --standalone
  --resource-path="$work_dir:$script_dir:$source_dir:."
  --output="$output_file"
)

if [[ -n "$reference_doc" ]]; then
  pandoc_args+=(--reference-doc="$reference_doc")
fi

pandoc "${pandoc_args[@]}"
python3 "$script_dir/format-docx.py" "$output_file" "$preamble_file"
echo "Created $output_file"

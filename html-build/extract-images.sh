#!/usr/bin/env bash
set -euo pipefail

pdf_file="${1:-images.pdf}"
map_file="${2:-mdlayout-images-pages.tex}"
script_dir="$(cd "$(dirname "$0")" && pwd)"
target="$script_dir/images"
mkdir -p "$target"
work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT

while read -r name page; do
  pdftoppm -f "$page" -l "$page" -singlefile -png -r 120 \
    "$pdf_file" "$work_dir/$name"
  converted="$work_dir/$name.webp"
  if command -v magick >/dev/null 2>&1; then
    magick "$work_dir/$name.png" -strip -resize '1100x1100>' -quality 84 "$converted"
  else
    convert "$work_dir/$name.png" -strip -resize '1100x1100>' -quality 84 "$converted"
  fi
  [[ -s "$converted" ]] || { echo "Image conversion failed: $name" >&2; exit 1; }
  mv "$converted" "$target/$name.webp"
done < <(sed -nE 's/.*imagepage@([^\\]+)\\endcsname\{([0-9]+)\}.*/\1 \2/p' "$map_file")

echo "Created images in $target"

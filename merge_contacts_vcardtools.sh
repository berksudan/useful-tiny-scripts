#!/usr/bin/env bash
# Merge+dedupe every contacts_*.vcf in DIR (default: cwd) into one new
# contacts_<timestamp>.vcf, using https://github.com/mbideau/vcardtools
set -euo pipefail
trap '[[ $? -eq 0 ]] && { echo; echo "================================="; read -rp "All operation successful, press enter to exit..."; }' EXIT

DIR="$(cd "${1:-.}" && pwd)"
CACHE="${VCARDTOOLS_CACHE:-$HOME/.cache/vcardtools-merge}"
TOOL="$CACHE/vcardtools"
VENV="$CACHE/venv"

mkdir -p "$CACHE"
[[ -d "$TOOL" ]] || git clone --quiet --depth 1 https://github.com/mbideau/vcardtools.git "$TOOL"
[[ -d "$VENV" ]] || { python3 -m venv "$VENV"; "$VENV/bin/pip" install -q wheel vobject fuzzywuzzy; }

shopt -s nullglob
files=("$DIR"/contacts_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9][0-9][0-9].vcf)
[[ ${#files[@]} -gt 1 ]] || { echo "[INFO] Nothing to merge: found ${#files[@]} contacts_*.vcf file(s) in $DIR"; exit 0; }

# Drop fully-empty vCards (no fields at all) -- vcardtools crashes on those.
CLEANDIR="$(mktemp -d "$CACHE/clean.XXXXXX")"
for f in "${files[@]}"; do
    "$VENV/bin/python" -c '
import sys
cards = ["BEGIN:VCARD" + c for c in open(sys.argv[1], encoding="utf-8", errors="replace").read().split("BEGIN:VCARD") if c.strip()]
kept = [c for c in cards if any(l.strip() and not l.startswith(("BEGIN:VCARD", "VERSION:", "END:VCARD")) for l in c.splitlines())]
open(sys.argv[2], "w", encoding="utf-8").write("".join(kept))
' "$f" "$CLEANDIR/$(basename "$f")"
done

DESTDIR="$(mktemp -u "$CACHE/merge.XXXXXX")"
"$VENV/bin/python" "$TOOL/vcardtools.py" --merge --no-match-approx "$DESTDIR" "$CLEANDIR"/*.vcf

OUTFILE="$DIR/contacts_$(date +%Y%m%d_%H%M%S).vcf"
cat "$DESTDIR"/*.vcard > "$OUTFILE"
rm -rf "$DESTDIR" "$CLEANDIR"
trash-put "${files[@]}"

echo "[INFO] Merged ${#files[@]} file(s) -> $OUTFILE (sources moved to trash)"

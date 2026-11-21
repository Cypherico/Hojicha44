#!/usr/bin/env bash
# Fetch the pinned KLP Lame keycap STEP sources (CC-BY-SA-4.0).
# Idempotent; writes to /tmp/kbd-renders/keycaps (scratch — the build
# regenerates mesh assets from these on every run).
set -euo pipefail
DIR="${KEYCAP_DIR:-/tmp/kbd-renders/keycaps}"
COMMIT=8e4b89b484cafe3bcaced6b459a4e29660991a40
STAMP="pinned commit: $COMMIT"
BASE="https://raw.githubusercontent.com/braindefender/KLP-Lame-Keycaps/$COMMIT/STEP/Choc%20Stem%20%2B%20Choc%20Size"
VARIANTS=(Saddle Saddle_Tilted Saddle_Homing Normal Normal_Homing Normal_Tilted Thumb)
mkdir -p "$DIR"

if [ -f "$DIR/PINNED_SOURCE.txt" ] && [ "$(cat "$DIR/PINNED_SOURCE.txt")" = "$STAMP" ]; then
  complete=true
  for v in "${VARIANTS[@]}"; do
    if ! grep -q '^ISO-10303-21;' "$DIR/klp_${v}.step"; then
      complete=false
      break
    fi
  done
  if [ "$complete" = true ]; then
    printf '%s\n' "$STAMP"
    exit 0
  fi
fi

staged=$(mktemp -d "$DIR/.keycaps.XXXXXXXX")
trap 'rm -rf -- "$staged"' EXIT
for v in "${VARIANTS[@]}"; do
  f="$staged/klp_${v}.step"
  curl --fail --silent --show-error --location --output "$f" \
    "$BASE/Choc_Stem_Choc_Size_${v}.step"
  if ! grep -q '^ISO-10303-21;' "$f"; then
    printf 'Expected a STEP file for %s\n' "$v" >&2
    exit 1
  fi
done
rm -f -- "$DIR/PINNED_SOURCE.txt"
for v in "${VARIANTS[@]}"; do
  mv -- "$staged/klp_${v}.step" "$DIR/"
done
printf '%s\n' "$STAMP" > "$staged/PINNED_SOURCE.txt"
mv -- "$staged/PINNED_SOURCE.txt" "$DIR/"
printf '%s\n' "$STAMP"

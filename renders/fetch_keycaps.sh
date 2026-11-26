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

CHECKSUMS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/keycaps.sha256"
if [ -f "$DIR/PINNED_SOURCE.txt" ] && [ "$(cat "$DIR/PINNED_SOURCE.txt")" = "$STAMP" ] &&
   (cd "$DIR" && shasum -a 256 -c "$CHECKSUMS" >/dev/null 2>&1); then
  printf '%s\n' "$STAMP"
  exit 0
fi

staged=$(mktemp -d "$DIR/.keycaps.XXXXXXXX")
trap 'rm -rf -- "$staged"' EXIT
for v in "${VARIANTS[@]}"; do
  f="$staged/klp_${v}.step"
  curl --fail --silent --show-error --location --output "$f" \
    "$BASE/Choc_Stem_Choc_Size_${v}.step"
done
(cd "$staged" && shasum -a 256 -c "$CHECKSUMS")
rm -f -- "$DIR/PINNED_SOURCE.txt"
for v in "${VARIANTS[@]}"; do
  mv -- "$staged/klp_${v}.step" "$DIR/"
done
printf '%s\n' "$STAMP" > "$staged/PINNED_SOURCE.txt"
mv -- "$staged/PINNED_SOURCE.txt" "$DIR/"
printf '%s\n' "$STAMP"

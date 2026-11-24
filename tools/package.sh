#!/usr/bin/env bash
# Build the delivered `.hmod` from `content/` at the campaign pin, put the
# notices inside it, and check it with the same tool the registry runs.
#
# This port has no native half: the tier is `content`/`data`, so the artifact
# is one flat content `.hmod` and there is no `.hnmod`.
#
#   ports/tools/build-slot.sh run --job uv-pack --port ports/underground_villages \
#       --step package -- env CARGO_INCREMENTAL=0 ports/underground_villages/tools/package.sh
#
# `CARGO_HORIZON_MOD` may name a prebuilt `cargo-horizon-mod`; otherwise the
# tool is built from the pin (which is why this belongs in a build slot).
set -euo pipefail

PORT=$(cd "$(dirname "$0")/.." && pwd)
CAMPAIGN=$(cd "$PORT/../.." && pwd)
HORIZON=${HORIZON:-$CAMPAIGN/ports/_shared/pins/horizon-1d63e0a}
ID=$(basename "$PORT")
LOGS=$PORT/target/ladder
mkdir -p "$LOGS"
cd "$PORT"

tool() {
    if [ -n "${CARGO_HORIZON_MOD:-}" ]; then
        "$CARGO_HORIZON_MOD" horizon-mod "$@"
    else
        (cd "$PORT" && cargo run --locked --offline --quiet \
            --manifest-path "$HORIZON/crates/cargo-horizon-mod/Cargo.toml" -- horizon-mod "$@")
    fi
}

[ -f "$PORT/content/horizon-mod.toml" ] || { echo "missing $PORT/content/horizon-mod.toml" >&2; exit 1; }

echo "== build ==" | tee "$LOGS/package.log"
(cd "$PORT/content" && tool build) 2>&1 | tee -a "$LOGS/package.log"
cp "$PORT/content/target/horizon-mod/$ID.hmod" "$PORT/content/$ID.hmod"

echo "== notices ==" | tee -a "$LOGS/package.log"
python3 "$PORT/tools/notice.py" "$PORT/content/$ID.hmod" | tee -a "$LOGS/package.log"

echo "== check ==" | tee -a "$LOGS/package.log"
(cd "$PORT/content" && tool check "$ID.hmod") 2>&1 | tee -a "$LOGS/package.log"

echo "== artifact ==" | tee -a "$LOGS/package.log"
python3 - "$PORT/content/$ID.hmod" <<'PY' | tee -a "$LOGS/package.log"
import hashlib, sys, zipfile
path = sys.argv[1]
data = open(path, 'rb').read()
names = zipfile.ZipFile(path).namelist()
print(f"{path} size={len(data)} sha256={hashlib.sha256(data).hexdigest()} entries={len(names)}")
print("notices inside:", [n for n in names if n.startswith('LICENSE')] or "none")
PY

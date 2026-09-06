#!/usr/bin/env bash
# Render one template (plus core) in a scratch directory and validate the
# result with butane --strict, without touching the repo's config.bu.
#
# usage: render_check.sh <key> [metaconfig.yaml]
set -euo pipefail

key="${1:?usage: render_check.sh <key> [metaconfig.yaml]}"
meta="${2:-metaconfig.yaml}"
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
scratch="${SCRATCHPAD:-${TMPDIR:-/tmp}}/fcos-render-check-$key"

[ -f "$repo/templates/$key.yaml.j2" ] || { echo "no templates/$key.yaml.j2" >&2; exit 1; }
rm -rf "$scratch" && mkdir -p "$scratch"
ln -s "$repo/templates" "$scratch/templates"

# Keep only core (needed for a valid config) and the requested block.
python3 - "$repo/$meta" "$key" > "$scratch/meta.yaml" <<'EOF'
import sys, yaml
cfg = yaml.safe_load(open(sys.argv[1]))
key = sys.argv[2]
if key not in cfg:
    sys.exit(f"'{key}' has no block in {sys.argv[1]}")
sub = {k: cfg[k] for k in ("core", key) if k in cfg}
yaml.safe_dump(sub, sys.stdout, sort_keys=False)
EOF

cd "$scratch"
python3 "$repo/build_config.py" meta.yaml
docker run --interactive --rm quay.io/coreos/butane:release --pretty --strict < config.bu > config.ign
echo "butane --strict: OK"

# Print the rendered unit files so the reviewer sees the real text.
python3 - config.ign <<'EOF'
import sys, json, base64, gzip, urllib.parse
ign = json.load(open(sys.argv[1]))
for f in ign.get("storage", {}).get("files", []):
    c = f.get("contents", {})
    if "source" not in c or not f["path"].endswith((".container", ".pod", ".service", ".socket", ".volume", ".network")):
        continue
    head, data = c["source"].split(",", 1)
    raw = base64.b64decode(data) if ";base64" in head else urllib.parse.unquote_to_bytes(data)
    if c.get("compression") == "gzip":
        raw = gzip.decompress(raw)
    print(f"\n# ===== {f['path']}")
    print(raw.decode().rstrip())
EOF
echo
echo "scratch dir: $scratch"

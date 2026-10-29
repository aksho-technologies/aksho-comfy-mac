#!/bin/bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$HERE/mac-env.sh"
ROOT="${AKSHO_COMFY_ROOT:-$HOME/AkshoComfy}"
python3 "$HERE/browser_bridge.py" --root "$ROOT" --uninstall
echo "[AKSHO COMFY] The local certificate is out of your keychain. Delete $ROOT to remove the rest."
echo
read -r -p "Press return to close." _

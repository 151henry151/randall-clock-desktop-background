#!/usr/bin/env bash
# Copy Randall Clock image assets into web/assets/ for static deployment.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ASSETS_DIR="${SCRIPT_DIR}/assets"
SRC_DIR="${REPO_ROOT}/src/images"

mkdir -p "${ASSETS_DIR}"

copy_asset() {
  local name="$1"
  local src="${SRC_DIR}/${name}"
  local dest="${ASSETS_DIR}/${name}"

  if [[ -f "${src}" ]]; then
    cp "${src}" "${dest}"
    echo "Copied ${src} -> ${dest}"
    return 0
  fi
  return 1
}

GLOBE_OK=0
OVERLAY_OK=0

if copy_asset "base_globe.png"; then
  GLOBE_OK=1
fi

if copy_asset "stationary_overlay.png"; then
  OVERLAY_OK=1
fi

if [[ "${GLOBE_OK}" -eq 0 ]]; then
  echo "Warning: src/images/base_globe.png not found."
  echo "  Run the desktop Black Mode install first, or place base_globe.png manually in web/assets/."
fi

if [[ "${OVERLAY_OK}" -eq 0 ]]; then
  echo "Warning: src/images/stationary_overlay.png not found."
  echo "  Run the desktop Black Mode install first, or place stationary_overlay.png manually in web/assets/."
fi

if [[ "${GLOBE_OK}" -eq 1 && "${OVERLAY_OK}" -eq 1 ]]; then
  echo "Assets ready in ${ASSETS_DIR}"
  exit 0
fi

exit 1

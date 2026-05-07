#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
UI_DIR="${ROOT_DIR}/apps/desktop-ui"

if [[ ! -d "${UI_DIR}" ]]; then
  echo "未找到桌面前端目录: ${UI_DIR}" >&2
  exit 1
fi

bash "${SCRIPT_DIR}/copy-sidecar.sh"

(
  cd "${UI_DIR}"

  if [[ ! -d node_modules ]]; then
    npm ci
  fi

  npm run tauri:build -- "$@"
)

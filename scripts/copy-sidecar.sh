#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENGINE_PYTHON_DIR="${ROOT_DIR}/engine-python"
TAURI_BIN_DIR="${ROOT_DIR}/apps/desktop-ui/src-tauri/binaries"

is_windows() {
  case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*|Windows_NT) return 0 ;;
    *) return 1 ;;
  esac
}

resolve_engine_binary() {
  if [[ -n "${VD_ENGINE_BINARY:-}" ]]; then
    if [[ ! -f "${VD_ENGINE_BINARY}" ]]; then
      echo "VD_ENGINE_BINARY 指向的 Python 下载引擎不存在: ${VD_ENGINE_BINARY}" >&2
      exit 1
    fi
    echo "${VD_ENGINE_BINARY}"
    return
  fi

  local candidates=()
  if is_windows; then
    candidates+=("${ENGINE_PYTHON_DIR}/.venv/Scripts/vd-engine.exe")
    candidates+=("${ENGINE_PYTHON_DIR}/.venv/Scripts/vd-engine")
  else
    candidates+=("${ENGINE_PYTHON_DIR}/.venv/bin/vd-engine")
  fi

  local candidate
  for candidate in "${candidates[@]}"; do
    if [[ -f "${candidate}" ]]; then
      echo "${candidate}"
      return
    fi
  done

  echo "未找到 Python 下载引擎可执行文件。" >&2
  echo "请先构建/安装 engine-python，或通过 VD_ENGINE_BINARY 指定 vd-engine 路径。" >&2
  exit 1
}

if [[ "${TAURI_BIN_DIR}" != "${ROOT_DIR}/apps/desktop-ui/src-tauri/binaries" ]]; then
  echo "sidecar 输出路径异常: ${TAURI_BIN_DIR}" >&2
  exit 1
fi

ENGINE_BINARY="$(resolve_engine_binary)"
TARGET_NAME="vd-engine"
if is_windows; then
  TARGET_NAME="vd-engine.exe"
fi
TARGET_PATH="${TAURI_BIN_DIR}/${TARGET_NAME}"

mkdir -p "${TAURI_BIN_DIR}"
rm -f "${TAURI_BIN_DIR}/video-engine"
rm -f "${TAURI_BIN_DIR}/video-engine.cmd"
rm -f "${TAURI_BIN_DIR}/vd-engine"
rm -f "${TAURI_BIN_DIR}/vd-engine.exe"

cp "${ENGINE_BINARY}" "${TARGET_PATH}"
chmod +x "${TARGET_PATH}" || true

if [[ ! -f "${TARGET_PATH}" ]]; then
  echo "sidecar 资源校验失败，缺少 Python 下载引擎: ${TARGET_PATH}" >&2
  exit 1
fi

echo "Python 下载引擎 sidecar 已复制到: ${TARGET_PATH}"

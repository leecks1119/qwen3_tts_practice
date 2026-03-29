#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"

pick_python() {
  for cmd in python3.12 python3.13 python3.14 python3; do
    if command -v "${cmd}" >/dev/null 2>&1; then
      echo "${cmd}"
      return 0
    fi
  done
  return 1
}

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "[error] 이 스크립트는 macOS 전용입니다."
  exit 1
fi

if [[ "$(uname -m)" != "arm64" ]]; then
  echo "[warn] Apple Silicon(M1/M2/M3/M4) 환경이 아닙니다."
  echo "[warn] MLX 기반 실행은 Apple Silicon에서 가장 안정적으로 동작합니다."
fi

if ! xcode-select -p >/dev/null 2>&1; then
  echo "[error] Xcode Command Line Tools가 필요합니다."
  echo "먼저 아래 명령을 실행하세요:"
  echo "  xcode-select --install"
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    echo "[setup] ffmpeg를 설치합니다..."
    brew install ffmpeg
  else
    echo "[error] ffmpeg가 필요합니다."
    echo "Homebrew 설치 후 아래 명령을 실행하세요:"
    echo "  brew install ffmpeg"
    exit 1
  fi
fi

PYTHON_CMD="$(pick_python || true)"
if [[ -z "${PYTHON_CMD}" ]]; then
  echo "[error] python3.12 이상이 필요합니다."
  echo "권장 설치 예시:"
  echo "  brew install python@3.12"
  exit 1
fi

echo "[setup] Python: ${PYTHON_CMD}"
"${PYTHON_CMD}" - <<'PY'
import sys
major, minor = sys.version_info[:2]
if (major, minor) < (3, 12):
    raise SystemExit("Python 3.12 이상이 필요합니다.")
print(f"[setup] Python version OK: {sys.version.split()[0]}")
PY

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "[setup] 가상환경을 생성합니다: ${VENV_DIR}"
  "${PYTHON_CMD}" -m venv "${VENV_DIR}"
else
  echo "[setup] 기존 가상환경을 재사용합니다: ${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"

echo "[setup] pip 업그레이드"
python -m pip install --upgrade pip

echo "[setup] 패키지 설치"
pip install -r "${PROJECT_ROOT}/requirements.txt"

echo
echo "[done] 설치가 완료되었습니다."
echo "다음 명령으로 테스트하세요:"
echo "  source .venv/bin/activate"
echo "  python test.py"

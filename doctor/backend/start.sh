#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UNIFIED_BACKEND="$(cd "$SCRIPT_DIR/../../backend" && pwd)"
export TZB_BACKEND_ENTRY_LABEL="统一"
export PORT="8000"
exec "$UNIFIED_BACKEND/start.sh" "$@"

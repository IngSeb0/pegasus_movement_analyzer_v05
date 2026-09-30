#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-$HOME/pegasus-lab/pegasus_avance_semana_1_6}"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$BASE/pegasus_movement" "$BASE/tools"
cp -a "$HERE/pegasus_movement/." "$BASE/pegasus_movement/"
cp "$HERE/tools/analyze_run.py" "$BASE/tools/analyze_run.py"
chmod +x "$BASE/tools/analyze_run.py"
echo "Instalado en: $BASE"
echo "Prueba: cd $BASE && python3 tools/analyze_run.py --help"

#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="$PROJECT_ROOT/dist/android"
OUTPUT_APK="$OUTPUT_DIR/radar-de-streaming.apk"

cd "$PROJECT_ROOT"

if [[ -x "$PROJECT_ROOT/.venv/bin/flet" ]]; then
    FLET="$PROJECT_ROOT/.venv/bin/flet"
elif command -v flet >/dev/null 2>&1; then
    FLET="$(command -v flet)"
else
    echo "Flet CLI não encontrado. Crie o ambiente e instale flet-cli conforme README.md." >&2
    exit 1
fi

mkdir -p "$OUTPUT_DIR"
"$FLET" build apk --yes -v

if [[ ! -d "$PROJECT_ROOT/build/apk" ]]; then
    echo "A compilação terminou sem criar build/apk. Confira as mensagens acima." >&2
    exit 1
fi

APK_SOURCE="$(find "$PROJECT_ROOT/build/apk" -type f -name '*.apk' -print -quit)"
if [[ -z "$APK_SOURCE" ]]; then
    echo "Nenhum APK foi encontrado em build/apk. Confira a saída de flet build." >&2
    exit 1
fi

cp "$APK_SOURCE" "$OUTPUT_APK"
echo "APK pronto: $OUTPUT_APK"

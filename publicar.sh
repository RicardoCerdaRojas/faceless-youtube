#!/usr/bin/env bash
# Atajo para el publicador: activa (o crea) el entorno virtual y llama a publicar.py.
# Uso: ./publicar.sh subir episodios/010-algo
#      ./publicar.sh revisar episodios/0*
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  echo "Creando el entorno virtual (.venv) e instalando dependencias…"
  python3 -m venv .venv
  .venv/bin/pip install -q -r tools/publicar/requirements.txt
fi
exec .venv/bin/python tools/publicar/publicar.py "$@"

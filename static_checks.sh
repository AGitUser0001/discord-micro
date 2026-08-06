#!/bin/sh
cd "$(dirname "$0")" || exit 1
echo 'pyright:'
uv run pyright; status1=$?
echo 'check:'
uv run ruff check --fix --fixable F401,I,RUF010,RUF022,RUF023,RUF100,UP007,UP035,UP037,UP045,FURB162,SIM101,SIM102,SIM114,PYI034,C401,TRY203,ISC004 .; status2=$?
if [ $status1 -eq 0 ] && [ $status2 -eq 0 ]; then
  echo 'format:'
  uv run ruff format
fi

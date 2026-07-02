#!/usr/bin/env bash
# Clona todos os repositorios m15o listados em links_srht_m15o.txt na raiz do projeto.
# Pre-requisitos: git (obrigatorio), hg/Mercurial (obrigatorio para repos hg.sr.ht)
#
# Uso:
#   ./clone-repos.sh
#   ./clone-repos.sh --dry-run
#   DRY_RUN=1 ./clone-repos.sh

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIST_FILE="$SCRIPT_DIR/links_srht_m15o.txt"
DRY_RUN="${DRY_RUN:-0}"

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

write_status() {
  local level="$1"
  local name="$2"
  local message="${3:-}"
  if [[ -n "$message" ]]; then
    echo "[$level] $name - $message"
  else
    echo "[$level] $name"
  fi
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

repo_exists() {
  local dir="$1"
  [[ -d "$dir/.git" || -d "$dir/.hg" ]]
}

echo "=== clone-repos.sh ==="
echo "Diretorio: $SCRIPT_DIR"
echo "Lista: $LIST_FILE"
if [[ "$DRY_RUN" == "1" ]]; then
  echo "Modo: DRY-RUN"
fi
echo ""

if [[ ! -f "$LIST_FILE" ]]; then
  echo "ERRO: Arquivo nao encontrado: $LIST_FILE" >&2
  exit 1
fi

mapfile -t REPO_LINES < <(
  awk '
    /^[[:space:]]*2a\)|^[[:space:]]*2b\)|^[[:space:]]*3\)/ { in_section=1; next }
    /^[[:space:]]*4\)/ { in_section=0; exit }
    in_section {
      if (match($0, /https:\/\/(git|hg)\.sr\.ht\/~m15o\/[^[:space:]#"$]+/, m)) {
        url = substr($0, RSTART, RLENGTH)
        if (url !~ /\.tar\.gz$/) print url
      }
    }
  ' "$LIST_FILE" | awk '!seen[$0]++'
)

TOTAL=${#REPO_LINES[@]}
echo "Repositorios encontrados: $TOTAL"
echo ""

if [[ "$TOTAL" -eq 0 ]]; then
  echo "ERRO: Nenhum repositorio encontrado em $LIST_FILE" >&2
  exit 1
fi

NEEDS_HG=0
for url in "${REPO_LINES[@]}"; do
  if [[ "$url" == https://hg.sr.ht/* ]]; then
    NEEDS_HG=1
    break
  fi
done

if [[ "$DRY_RUN" != "1" ]]; then
  if ! command_exists git; then
    echo "ERRO: git nao encontrado no PATH." >&2
    exit 1
  fi
  if [[ "$NEEDS_HG" -eq 1 ]] && ! command_exists hg; then
    echo "ERRO: hg (Mercurial) nao encontrado no PATH." >&2
    exit 1
  fi
fi

OK=0
SKIP=0
FAIL=0
FAILED_NAMES=()

for url in "${REPO_LINES[@]}"; do
  name="${url##*/}"
  type="${url#https://}"
  type="${type%%.sr.ht/*}"
  target_dir="$SCRIPT_DIR/$name"

  if repo_exists "$target_dir"; then
    write_status "SKIP" "$name" "pasta ja existe"
    SKIP=$((SKIP + 1))
    continue
  fi

  if [[ -e "$target_dir" ]]; then
    write_status "SKIP" "$name" "pasta existe mas sem .git/.hg - nao sobrescrevendo"
    SKIP=$((SKIP + 1))
    continue
  fi

  if [[ "$DRY_RUN" == "1" ]]; then
    write_status "DRY-RUN" "$name" "$type clone $url"
    OK=$((OK + 1))
    continue
  fi

  write_status "CLONE" "$name" "$type $url"

  if [[ "$type" == "git" ]]; then
    if git clone "$url" "$target_dir"; then
      write_status "OK" "$name"
      OK=$((OK + 1))
    else
      write_status "FAIL" "$name" "git clone falhou"
      FAIL=$((FAIL + 1))
      FAILED_NAMES+=("$name")
      rm -rf "$target_dir" 2>/dev/null || true
    fi
  else
    if hg clone "$url" "$target_dir"; then
      write_status "OK" "$name"
      OK=$((OK + 1))
    else
      write_status "FAIL" "$name" "hg clone falhou"
      FAIL=$((FAIL + 1))
      FAILED_NAMES+=("$name")
      rm -rf "$target_dir" 2>/dev/null || true
    fi
  fi
done

echo ""
echo "=== Resumo ==="
echo "Total: $TOTAL | OK: $OK | SKIP: $SKIP | FAIL: $FAIL"

if [[ "$FAIL" -gt 0 ]]; then
  echo ""
  echo "Falharam:"
  for name in "${FAILED_NAMES[@]}"; do
    echo "  - $name"
  done
  exit 1
fi

exit 0

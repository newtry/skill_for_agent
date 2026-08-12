#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf '%s\n' \
    'Usage: verify_maven_change.sh --project PATH [--module MODULE] [--test TEST_CLASS] [--mode test|package] [--dry-run]' \
    '' \
    'Runs a focused Maven verification. It never commits, pushes, publishes, or deletes files.'
}

project_root=""
module=""
test_class=""
mode="test"
dry_run=0

while (($# > 0)); do
  case "$1" in
    --project)
      [[ $# -ge 2 ]] || { printf '%s\n' '--project requires a path' >&2; exit 2; }
      project_root="$2"
      shift 2
      ;;
    --module)
      [[ $# -ge 2 ]] || { printf '%s\n' '--module requires a Maven module' >&2; exit 2; }
      module="$2"
      shift 2
      ;;
    --test)
      [[ $# -ge 2 ]] || { printf '%s\n' '--test requires a test class' >&2; exit 2; }
      test_class="$2"
      shift 2
      ;;
    --mode)
      [[ $# -ge 2 ]] || { printf '%s\n' '--mode requires test or package' >&2; exit 2; }
      mode="$2"
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown option: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

[[ -n "$project_root" ]] || { printf '%s\n' '--project is required' >&2; usage >&2; exit 2; }
[[ -d "$project_root" ]] || { printf 'Project directory not found: %s\n' "$project_root" >&2; exit 2; }
[[ -f "$project_root/pom.xml" ]] || { printf 'No pom.xml under project directory: %s\n' "$project_root" >&2; exit 2; }
[[ "$mode" == "test" || "$mode" == "package" ]] || { printf 'Unsupported mode: %s\n' "$mode" >&2; exit 2; }
[[ -z "$test_class" || "$mode" == "test" ]] || { printf '%s\n' '--test can only be used with --mode test' >&2; exit 2; }

maven_bin="${MAVEN_BIN:-mvn}"
if ! command -v "$maven_bin" >/dev/null 2>&1; then
  printf 'Maven executable not found: %s\n' "$maven_bin" >&2
  exit 127
fi

command_args=()
if [[ -n "$module" ]]; then
  command_args+=(-pl "$module" -am)
fi
if [[ "$mode" == "test" ]]; then
  if [[ -n "$test_class" ]]; then
    command_args+=("-Dtest=$test_class" '-Dsurefire.failIfNoSpecifiedTests=false')
  fi
  command_args+=(test)
else
  command_args+=(-DskipTests package)
fi

printf 'Project: %s\n' "$project_root"
printf 'Command:'
printf ' %q' "$maven_bin" "${command_args[@]}"
printf '\n'

if ((dry_run)); then
  exit 0
fi

cd "$project_root"
exec "$maven_bin" "${command_args[@]}"

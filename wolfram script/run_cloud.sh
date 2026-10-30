#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "$script_dir/.." && pwd)"
workbook="$repo_dir/collected_data_20221101_JUB Survey on Renaming (Responses) - Anonymised.xlsx"
output="${1:-$script_dir/results/survey-analysis.pdf}"
wolframscript_bin="${WOLFRAMSCRIPT:-wolframscript}"

if ! command -v "$wolframscript_bin" >/dev/null 2>&1; then
    printf 'ERROR: WolframScript CLI not found: %s\n' "$wolframscript_bin" >&2
    printf 'Install/configure the WolframScript client for Wolfram Cloud, then retry.\n' >&2
    exit 1
fi

if [[ ! -f "$workbook" ]]; then
    printf 'ERROR: Survey workbook not found: %s\n' "$workbook" >&2
    exit 1
fi

mkdir -p "$(dirname -- "$output")"
temporary_output="$(mktemp "${TMPDIR:-/tmp}/wolfram-survey.XXXXXX")"
trap 'rm -f -- "$temporary_output"' EXIT

printf 'Uploading the anonymized workbook to Wolfram Cloud for this evaluation...\n' >&2
base64 -w 0 "$workbook" |
    "$wolframscript_bin" -cloud -file "$script_dir/analyze_survey.wls" \
        -print -format PDF >"$temporary_output"

if [[ ! -s "$temporary_output" ]] ||
    [[ "$(head -c 5 "$temporary_output")" != '%PDF-' ]]; then
    printf 'ERROR: WolframScript did not return a valid PDF. Check cloud authentication and kernel output.\n' >&2
    exit 1
fi

mv -- "$temporary_output" "$output"
printf 'Wrote survey report: %s\n' "$output"

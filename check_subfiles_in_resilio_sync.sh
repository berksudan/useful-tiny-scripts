#!/usr/bin/env bash

set -euo pipefail
trap '[[ $? -eq 0 ]] && { echo; echo "================================="; read -rp "All operation successful, press enter to exit..."; }' EXIT

#===============================================================================
# Script: maintenance.sh
# Purpose:
#   Search for files excluding certain patterns/directories and report
#===============================================================================

#------------------------------------------------------------------------------
# Function: escape_for_find
# Description:
#   Escape glob-special characters in a string so it can be safely used with
#   `find -path` patterns.
# Arguments:
#   $1 - input string to escape
# Returns:
#   Escaped string
#------------------------------------------------------------------------------
escape_for_find() {
  local input="$1"
  input="${input//\\/\\\\}"   # escape backslashes
  input="${input//\*/\\*}"       # escape *
  input="${input//\?/\\?}"       # escape ?
  input="${input//[/\\[}"         # escape [
  input="${input//]/\\]}"         # escape ]
  printf '%s' "$input"
}

#------------------------------------------------------------------------------
# Function: find_and_report
# Description:
#   Find all regular files under a base directory, excluding given file patterns
#   and directories, then print a success or warning message.
# Globals:
#   SCRIPT_NAME
# Arguments:
#   $1 - base directory to search
#   Remaining args - names of directories to exclude (basename only)
# Returns:
#   prints results to stdout
#------------------------------------------------------------------------------
find_and_report() {
  local base_dir="$1"
  shift
  local -a excluded_dirs=("$@")

  # Build find arguments
  local -a args=(find "$base_dir" -type f \
    ! -name '*.webp' \
    ! -name '.trashed-*' \
    ! -name '.nomedia' \
    ! -name "$SCRIPT_NAME")

  # Append exclusions for each directory
  for dir in "${excluded_dirs[@]}"; do
    local esc_dir; esc_dir=$(escape_for_find "$dir")
    # exclude files in ./<dir>/*
    args+=( ! -path "${base_dir}/${esc_dir}/*" )
    # exclude files in ./<any>/<dir>/*
    args+=( ! -path "${base_dir}/*/${esc_dir}/*" )
  done

  # Execute
  local results
  results="$("${args[@]}")"

  if [[ -z "$results" ]]; then
    echo -e "\033[1;96m[SUCCESS] No files found under '$base_dir' after exclusions.\033[0m"
  else
    echo -e "\033[1;31m[WARNING] Files found under '$base_dir':\033[0m"
    echo "$results"
  fi
}

#===============================================================================
# Main
#===============================================================================

# Name of this script for self-exclusion (override via $2, else BASH_SOURCE)
SCRIPT_NAME="${2:-$(basename "${BASH_SOURCE[0]}")}"

# Directories to exclude in find_and_report (basenames)
EXCLUDED_DIRS=(
  "Audiobooks"
  ".Links"
  ".thumbnails"
  ".sync"
)

# Run find & report from BASE_DIR, passing exclusion list
BASE_DIR="$(cd "${1:-.}" >/dev/null && pwd)"
find_and_report "$BASE_DIR" "${EXCLUDED_DIRS[@]}"

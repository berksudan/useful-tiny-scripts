#!/usr/bin/env bash

set -euo pipefail
trap '[[ $? -eq 0 ]] && { echo; echo "================================="; read -rp "All operation successful, press enter to exit..."; }' EXIT

#===============================================================================
# Script: maintenance.sh
# Purpose:
#   1) Search for files excluding certain patterns/directories and report
#   2) Move all but the newest file in Contacts/ to trash
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

#------------------------------------------------------------------------------
# Function: trash_all_but_newest
# Description:
#   Trash all but the most recent file in the given directory (non-recursive).
# Arguments:
#   $1 - target directory
#------------------------------------------------------------------------------
trash_all_but_newest() {
  local target_dir="$1"

  if [[ ! -d "$target_dir" ]]; then
    echo "Error: Directory '$target_dir' not found." >&2
    return 1
  fi

  # Find regular files, sort lexicographically, drop the newest (last) and trash the rest
  find "$target_dir" -maxdepth 1 -type f ! -name '.*' \
    | sort \
    | head -n -1 \
    | while IFS= read -r file; do
        gio trash "$file"
        echo "Trashed: $file"
      done
}

#===============================================================================
# Main
#===============================================================================

# Get the name of this script for self-exclusion
SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"

# Directories to exclude in find_and_report (basenames)
EXCLUDED_DIRS=(
  "Audiobooks"
  ".Links"
  ".thumbnails"
  ".sync"
)

# 1) Trash all but newest in Contacts subdirectory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null && pwd)"
CONTACTS_DIR="$BASE_DIR/Contacts"
trash_all_but_newest "$CONTACTS_DIR"


# 2) Run find & report from current directory, passing exclusion list
find_and_report "." "${EXCLUDED_DIRS[@]}"

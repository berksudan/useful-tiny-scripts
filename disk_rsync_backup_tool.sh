#!/bin/bash

# Description:
# This script facilitates backing up files from a source directory to the current directory.
# It performs the following tasks:
# 1. Asks for confirmation of the source directory, with an option to specify a different one.
# 2. Checks if the source directory is mounted.
# 3. Displays the content of the source directory and confirms its correctness.
# 4. Executes a dry run of `rsync` to show what would be backed up or deleted.
# 5. Asks for confirmation to proceed with the actual `rsync` backup.
# 6. Excludes the script itself, common system directories, and temporary files during the backup.
# 
# Usage:
# 1. Place this script on your backup disk (the disk where you want to store backups).
# 2. Set the DEF_SOURCE_DIR path to point to your main disk (the disk with the files to back up).
# 3. Run this script in a Linux terminal.
# 4. Follow the prompts to verify directory paths and contents.
# 5. The script will perform a dry run and, if confirmed, execute the actual backup.

DEF_SOURCE_DIR="/media/${USER}/T7 Shield/"

echo_info() {
    echo -e "\033[0;36m[INFO] $1\033[0m"
}

echo_error() {
    echo -e "\e[91m[ERROR] $1\e[0m"
}

echo_question() {
    echo -n -e "\e[33m[QUESTION] $1\e[0m"
}

echo_question "Is it the source directory: '$DEF_SOURCE_DIR'? [Y/n]: " && read yn
    case $yn in
        Y|y|"") source_dir=$DEF_SOURCE_DIR;;  
        N|n|*) read -p "Please enter the source directory: " source_dir ;;
    esac


if ! mountpoint -q "${source_dir}"
then
  echo_error "The source directory: '${source_dir}' could not be mounted. Verify this by running: 'mount -l'\nexiting.."
  exit 1
else
  echo_info "The source directory: '${source_dir}' is successfully mounted."
fi


echo_info "Content of the source directory: '$source_dir':"
ls -la "$source_dir"
echo_question "Is it the content of the source directory? [Y/n]: " && read yn
    case $yn in
        Y|y|"") ;;  
        N|n|*) echo_info "exiting.."; exit 1 ;;
    esac

backup_bash_filename=`basename "$0"`

echo_info "You will see a DRY RUN out of rsync, in a few moment.."
rsync --dry-run -avhP --delete \
    --exclude $backup_bash_filename \
    --exclude '$RECYCLE.BIN/' \
    --exclude 'System Volume Information' \
    --exclude '.Trash-1000' \
    --exclude 'Films & Series & Games/Films' \
    --exclude 'Films & Series & Games/Series' \
    "$source_dir" "./" | grep --color=always "deleting\|$"

echo "-----------------------------"

# Confirm actual rsync
echo_question "Proceed with the actual rsync? [y/N]: " && read yn
    case $yn in
        N|n|"") echo_info "exiting.."; exit 1 ;;
        Y|y|*) rsync -avh --delete \
    --exclude $backup_bash_filename \
    --exclude '$RECYCLE.BIN/' \
    --exclude 'System Volume Information' \
    --exclude '.Trash-1000' \
    --exclude 'Films & Series & Games/Films' \
    --exclude 'Films & Series & Games/Series' \
    "$source_dir" "./" | grep --color=always "deleting\|$" ;;
    esac

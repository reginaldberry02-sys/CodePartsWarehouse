#!/usr/bin/env bash
# Wrapper to call bulk_register_scripts from anywhere

set -e

# Go to DocTools where bulk_register_scripts.py lives
cd "/Users/reginaldberry/Library/Mobile Documents/com~apple~CloudDocs/Downloads/Chats/Projects/MacOS Automations/RegScriptBox/Scripts/DocTools"

# Pass all args through
python3 bulk_register_scripts.py "$@"

#!/bin/bash

set -o pipefail
umask 077
cd -- "$(dirname -- "$0")" || exit 1

log_dir="$HOME/Library/Logs/FOCAL"
mkdir -p "$log_dir" || exit 1
log_file="$log_dir/focal.log"

run_focal() {
    if [ ! -x ./venv/bin/python3 ]; then
        # Alfred omits absolute symlinks during import. Rebuild them locally,
        # keeping the bundled dependencies and the same Python minor version.
        local python_home python_version base_python
        python_home="$(sed -n 's/^home = //p' venv/pyvenv.cfg)" || return 1
        python_version="$(sed -nE 's/^version = ([0-9]+\.[0-9]+).*/\1/p' venv/pyvenv.cfg)" || return 1
        base_python="$python_home/python$python_version"
        if [ -z "$python_home" ] || [ -z "$python_version" ] || [ ! -x "$base_python" ]; then
            printf 'Error: Python %s is unavailable at %s. Run ./install.sh from the FOCAL checkout to rebuild.\n' "$python_version" "$base_python" >&2
            return 1
        fi
        printf 'Restoring local Python %s interpreter links...\n' "$python_version"
        "$base_python" -m venv --without-pip ./venv || return 1
    fi
    ./venv/bin/python3 create_event.py "$@"
}

{
    printf '\n--- FOCAL %s ---\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
    run_focal "$@"
} 2>&1 | tee -a "$log_file"
status=${PIPESTATUS[0]}

if [ "$status" -ne 0 ]; then
    printf 'FOCAL failed (exit %s). See %s\n' "$status" "$log_file" >&2
    /usr/bin/osascript -e 'display notification "Event not created. See ~/Library/Logs/FOCAL/focal.log" with title "FOCAL failed"' >&2
fi

exit "$status"

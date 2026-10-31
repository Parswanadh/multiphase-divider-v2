#!/usr/bin/env bash
# Start the CadenceVM VirtualBox GUI window.
# If the VM is already running, do not start it again; explain how to open its window.
# Usage: start_vm_gui.sh
set -euo pipefail

VM="${VM_NAME:-CadenceVM}"

if ! info=$(VBoxManage showvminfo "$VM" --machinereadable 2>/dev/null); then
    echo "error: VM '$VM' not found (check with: VBoxManage list vms)" >&2
    exit 1
fi

state=$(printf '%s\n' "$info" | sed -n 's/^VMState="\(.*\)"$/\1/p')
session=$(printf '%s\n' "$info" | sed -n 's/^SessionName="\(.*\)"$/\1/p')

if [ "$state" = "running" ]; then
    echo "$VM is already running (session: ${session:-unknown}). Not starting it again."
    if [ "$session" = "headless" ]; then
        echo "It has no window. To open one: run 'VirtualBox &', select $VM, click Show."
    else
        echo "Its window should already be open. Switch to the VirtualBox window."
    fi
    exit 0
fi

if [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
    echo "error: no graphical display in this shell (DISPLAY/WAYLAND_DISPLAY unset)." >&2
    echo "Run this script from a terminal inside your desktop session." >&2
    exit 1
fi

echo "$VM state is '$state'. Starting the GUI..."
VBoxManage startvm "$VM" --type gui
echo "Started. Log in inside the VM window (see vm/README.md)."

#!/usr/bin/env bash
# Clean shutdown of CadenceVM: sends an ACPI power-button event and waits.
# Usage: stop_vm.sh [--timeout SECONDS] [--force]
#   default timeout is 180 s. Without --force the VM is never powered off hard.
#   --force : after the timeout, power off immediately (possible data loss,
#             fsck on next boot).
set -euo pipefail

VM="${VM_NAME:-CadenceVM}"
TIMEOUT=180
FORCE=0

while [ $# -gt 0 ]; do
    case "$1" in
        --force) FORCE=1 ;;
        --timeout)
            shift
            TIMEOUT="${1:-}"
            ;;
        -h|--help)
            sed -n '2,6p' "$0"
            exit 0
            ;;
        *)
            echo "unknown option: $1" >&2
            exit 2
            ;;
    esac
    shift
done

case "$TIMEOUT" in
    ''|*[!0-9]*) echo "error: --timeout must be a whole number of seconds" >&2; exit 2 ;;
esac

get_state() {
    VBoxManage showvminfo "$VM" --machinereadable | sed -n 's/^VMState="\(.*\)"$/\1/p'
}

state=$(get_state)
case "$state" in
    poweroff|aborted)
        echo "$VM is already powered off."
        exit 0
        ;;
    running)
        ;;
    *)
        echo "$VM is in state '$state'; this script only shuts down a running VM." >&2
        echo "If it is paused, resume it from the VirtualBox window first." >&2
        exit 1
        ;;
esac

echo "Sending ACPI power button to $VM (timeout ${TIMEOUT}s)..."
VBoxManage controlvm "$VM" acpipowerbutton

waited=0
while [ "$(get_state)" = "running" ] && [ "$waited" -lt "$TIMEOUT" ]; do
    sleep 2
    waited=$((waited + 2))
done

if [ "$(get_state)" != "running" ]; then
    echo "$VM powered off cleanly after about ${waited}s."
    exit 0
fi

echo "$VM is still running after ${TIMEOUT}s." >&2
echo "The guest may be showing a shutdown dialog (look at the VM window), or a job may be running." >&2
echo "Shut down from inside the guest, then run this script again." >&2

if [ "$FORCE" -eq 1 ]; then
    echo "--force given: forcing power off now. Unsaved guest data may be lost." >&2
    VBoxManage controlvm "$VM" poweroff
    echo "$VM powered off (forced). The guest will check its disks on next boot."
    exit 0
fi

echo "Not forcing. Re-run with --force only if you accept possible data loss." >&2
exit 1

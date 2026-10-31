#!/usr/bin/env bash
# Pack files/directories into an ISO and attach it to the CadenceVM DVD drive.
# The guest sees the ISO at /media/<ISO_LABEL> (automount; verify in the guest).
# Works whether the VM is running or stopped.
#
# Usage: [ISO_LABEL=TO_VM] send_to_vm.sh <file-or-dir> [more ...]
#   ISO_LABEL : volume label, 1-32 chars, A-Z 0-9 _ (default TO_VM)
#   OUTDIR    : where the ISO is written (default /home/parshu/vm)
# Note: this replaces whatever is currently in the VM's DVD drive.
set -euo pipefail

VM="${VM_NAME:-CadenceVM}"
LABEL="${ISO_LABEL:-TO_VM}"
OUTDIR="${OUTDIR:-/home/parshu/vm}"
CTL="IDE"
PORT=0
DEV=0

die() { echo "error: $*" >&2; exit 1; }

if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "usage: [ISO_LABEL=NAME] $0 <file-or-dir> [more ...]" >&2
    exit 2
fi

command -v xorriso >/dev/null 2>&1 || die "xorriso is not installed"
command -v VBoxManage >/dev/null 2>&1 || die "VBoxManage is not installed"

if ! [[ "$LABEL" =~ ^[A-Z0-9_]{1,32}$ ]]; then
    die "ISO_LABEL must be 1-32 characters: A-Z, 0-9, underscore (got '$LABEL')"
fi

VBoxManage showvminfo "$VM" --machinereadable >/dev/null 2>&1 || die "VM '$VM' not found"

abs=()
for p in "$@"; do
    [ -e "$p" ] || die "no such file or directory: $p"
    abs+=("$(realpath "$p")")
done

info=$(VBoxManage showvminfo "$VM" --machinereadable)
prev=$(printf '%s\n' "$info" | sed -n 's/^"IDE-0-0"="\(.*\)"$/\1/p')
echo "DVD drive currently holds: ${prev:-none} (this will be replaced)"

mkdir -p "$OUTDIR"
ts=$(date +%Y%m%d_%H%M%S)
ISO="$OUTDIR/send_${ts}.iso"

echo "Building ISO $ISO (label $LABEL) from ${#abs[@]} item(s)..."
xorriso -as mkisofs -r -J -joliet-long -V "$LABEL" -o "$ISO" "${abs[@]}"

echo "Attaching ISO to $VM ($CTL port $PORT device $DEV)..."
VBoxManage storageattach "$VM" --storagectl "$CTL" --port "$PORT" --device "$DEV" \
    --type dvddrive --medium "$ISO" --forceunmount

now=$(VBoxManage showvminfo "$VM" --machinereadable | sed -n 's/^"IDE-0-0"="\(.*\)"$/\1/p')
[ "$now" = "$ISO" ] || die "attach check failed: DVD drive shows '$now'"

echo
echo "Done. In the guest the files are at:  /media/$LABEL"
echo "If it is not there after a few seconds, in a guest terminal run:"
echo "    ls /media ; sudo mount /dev/sr0 /mnt   (verify device name)"
echo "Copy what you need out of that folder to ~/ before you rely on it."

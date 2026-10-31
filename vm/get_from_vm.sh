#!/usr/bin/env bash
# Pull a tar file out of the CadenceVM guest through the scratch disk.
#
# The guest writes a tar onto the raw scratch disk (SCSI port 1, appears as /dev/sdb).
# The host reads it back: clone the disk to RAW, then take the first SIZE bytes.
#
# Modes:
#   get_from_vm.sh guest
#       Print the commands to run INSIDE the guest (no host changes).
#   get_from_vm.sh host <SIZE_BYTES> <DEST_DIR> [MD5]
#       Host side. VM must be powered off (stop_vm.sh first).
#       SIZE_BYTES is the byte count the guest printed (stat -c%s).
#       MD5 is optional; if given it is compared with the pulled tar.
set -euo pipefail

VM="${VM_NAME:-CadenceVM}"
SCRATCH_PORT_KEY='SCSI-1-0'          # scratch disk: SCSI controller, port 1
SCRATCH_BYTES=536870912              # 512 MB
WORKDIR="${WORKDIR:-/home/parshu/vm}"

die() { echo "error: $*" >&2; exit 1; }

usage() {
    sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
}

guest_steps() {
    cat <<'EOF'
Run these in a terminal INSIDE the guest (CadenceVM).

1. Make the tar (adjust the source folder; must be under 512 MB):
     tar -cf /tmp/results.tar -C ~/gpdk_run out

2. Check it, then write it to the scratch disk. Paste as one block; the
   parentheses keep any "exit" from closing your terminal:

     (
       SIZE=$(stat -c%s /tmp/results.tar)
       [ "$SIZE" -le 536870912 ] || { echo "tar too big"; exit 1; }
       [ "$(sudo blockdev --getsize64 /dev/sdb)" -eq 536870912 ] || { echo "/dev/sdb is not the 512 MB scratch disk"; exit 1; }
       if mount | grep -q '^/dev/sdb'; then echo "/dev/sdb is mounted"; exit 1; fi
       sudo dd if=/tmp/results.tar of=/dev/sdb bs=1M conv=fsync
       sync
       echo "SIZE=$SIZE"
       echo "MD5=$(md5sum < /tmp/results.tar | cut -d' ' -f1)"
     )

3. Note the SIZE and MD5 lines. Then, on the host, stop the VM
   (vm/stop_vm.sh) and run:
     vm/get_from_vm.sh host <SIZE> <DEST_DIR> <MD5>

Do not mount or format /dev/sdb in the guest. Do not run dd on /dev/sda.
EOF
}

host_pull() {
    local size="${1:-}" dest="${2:-}" md5want="${3:-}"

    [[ "$size" =~ ^[0-9]+$ ]] || die "SIZE_BYTES must be a whole number (got '$size')"
    [ "$size" -gt 0 ] || die "SIZE_BYTES must be greater than 0"
    [ "$size" -le "$SCRATCH_BYTES" ] || die "SIZE_BYTES $size is larger than the scratch disk ($SCRATCH_BYTES)"
    [ -n "$dest" ] || die "DEST_DIR is required"

    command -v VBoxManage >/dev/null 2>&1 || die "VBoxManage not installed"
    command -v realpath >/dev/null 2>&1 || die "realpath not installed"

    local info state src
    info=$(VBoxManage showvminfo "$VM" --machinereadable) || die "VM '$VM' not found"
    state=$(printf '%s\n' "$info" | sed -n 's/^VMState="\(.*\)"$/\1/p')
    [ "$state" = "poweroff" ] || [ "$state" = "aborted" ] || \
        die "$VM is '$state'. A running VM locks its disk. Run vm/stop_vm.sh first."

    # Read the scratch disk path from the VM config at run time. Do not hardcode it:
    # if a snapshot was taken, the attachment may point elsewhere.
    src=$(printf '%s\n' "$info" | sed -n "s/^\"$SCRATCH_PORT_KEY\"=\"\(.*\)\"\$/\1/p")
    [ -n "$src" ] && [ "$src" != "none" ] || die "no disk attached at $SCRATCH_PORT_KEY on $VM"
    [ -f "$src" ] || die "scratch medium file not found: $src"

    mkdir -p "$dest" "$WORKDIR"
    dest=$(realpath "$dest")

    # Fresh temp dir for the raw clone (clonemedium refuses an existing target).
    local tmp raw out
    tmp=$(mktemp -d "$WORKDIR/.pull.XXXXXX")
    raw="$tmp/scratch.raw"
    # Expand now: locals are gone when the EXIT trap fires.
    trap "VBoxManage closemedium disk '$raw' >/dev/null 2>&1 || true; rm -rf '$tmp'" EXIT

    echo "Cloning $src to RAW (needs about 512 MB free in $WORKDIR)..."
    VBoxManage clonemedium disk "$src" "$raw" --format RAW

    out="$dest/results.tar"
    head -c "$size" "$raw" > "$out"

    [ "$(stat -c%s "$out")" -eq "$size" ] || die "short read: got $(stat -c%s "$out") of $size bytes"
    tar -tf "$out" >/dev/null || die "pulled file is not a readable tar: $out"

    local md5got
    md5got=$(md5sum "$out" | cut -d' ' -f1)
    if [ -n "$md5want" ]; then
        [ "$md5got" = "$md5want" ] || die "md5 mismatch: host $md5got, guest $md5want"
        echo "md5 matches the guest."
    fi

    echo "OK: $out ($size bytes, md5 $md5got)"
    echo "Unpack with: tar -xf \"$out\" -C \"$dest\""
}

case "${1:-}" in
    guest) guest_steps ;;
    host)  shift; host_pull "$@" ;;
    -h|--help|"") usage ;;
    *) die "unknown mode '$1' (use: guest | host | --help)" ;;
esac

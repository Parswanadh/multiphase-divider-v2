# CadenceVM: beginner guide

The Cadence (Virtuoso/Spectre) machine is a CentOS 6.5 virtual machine that
runs in **VirtualBox** on this Linux host. The VM is named `CadenceVM`.

VMware is **not** installed on this host. Only VirtualBox is. The original
`.vmx` VMware file is on the pen drive. You can open that in VMware
Workstation on another machine, but not here.

Do not run the VM from the pen drive. Always use the copy on the host disk
(`/home/parshu/vm/`).

---

## 1. Open the VM window

From this repo:

```
vm/start_vm_gui.sh
```

- If the VM is off, this starts it with a window.
- If it is already running, the script says so and does not start it again.
  In that case, run `VirtualBox &`, select **CadenceVM**, and click **Show**.

## 2. Log in

The guest logs in automatically as user `buet`. If you get a login screen,
use the password from the original install guide. It is not repeated here.

## 3. Open a terminal

Right-click the desktop, or use the applications menu, and choose
**Terminal**.

## 4. Start Virtuoso

```
cd ~/cds_work          # verify: the folder that contains cds.lib
virtuoso &
```

Virtuoso must be started from the folder that holds `cds.lib`. Otherwise it
cannot find your libraries.

### Add the gpdk045 PDK to cds.lib (verify)

Add this line to `~/cds_work/cds.lib`:

```
DEFINE gpdk045 /home/buet/pdk/gpdk045_v_6_0/gpdk045
```

- The PDK's own `cds.lib`, `pvtech.lib` and `assura_tech.lib` sit next to
  that folder. Check with `ls ~/pdk/gpdk045_v_6_0/` (verify).
- You can also add the library through the Library Manager in the CIW
  window. Either way, restart Virtuoso after editing `cds.lib`.

## 5. Run Spectre by hand

In a terminal inside the guest:

```
cd ~/gpdk_run
./run_gpdk045.sh . one
```

- The arguments are as given in the run notes. Verify what `.` and `one`
  mean by reading the script first: `less run_gpdk045.sh`.
- Results go to `~/gpdk_run/out` (verify).
- `divider_gpdk45.scs` in that folder is the netlist that gets simulated.

## 6. Move files in and out

**Host to guest** (on the host):

```
ISO_LABEL=TO_VM vm/send_to_vm.sh path/to/file_or_dir
```

This builds an ISO and attaches it to the VM's DVD drive. The guest sees
the files at `/media/TO_VM`. Copy anything you need into `~/` before you
rely on it.

Note: this **replaces** whatever is in the DVD drive (currently
`rpms_in.iso`).

**Guest to host:** see `vm/get_from_vm.sh`. Run `vm/get_from_vm.sh guest`
to print the guest steps. The VM must be powered off for the host step.

## 7. Snapshots and rollback

The VM has a snapshot called **`pristine`**. It was taken before the first
boot.

**Before an experiment**, take a snapshot so you can go back:

- In the VirtualBox window: **Machine > Take Snapshot** (verify the menu
  name in your version).
- Or on the host: `VBoxManage snapshot CadenceVM take "before-<what>"`
  (verify).

**To roll back to a clean machine:**

1. Power off the VM (`vm/stop_vm.sh`).
2. In VirtualBox: select CadenceVM, open **Snapshots**, select `pristine`,
   and click **Restore** (verify).

Restoring discards everything done since the snapshot, including your
files and results. Copy out anything you need first.

Restoring also returns the VM's settings to what they were at `pristine`.
If the scratch disk (`/home/parshu/vm/scratch.vdi`) or the 2222 port
forward were added after `pristine`, they will be missing after a restore.
Re-add them in VirtualBox settings (verify).

## 8. Troubleshooting

| Symptom | What to do |
|---|---|
| Black screen or no window | The VM may be running with no window. Run `VirtualBox &`, select CadenceVM, click **Show**. If the VM is off, use `vm/start_vm_gui.sh`. Wait a minute after start, since the first boot is slow. |
| Mouse does not work or is stuck in the window | The host key (default **Right Ctrl**) releases the mouse. There are no Guest Additions, so click inside the window to capture the mouse again. |
| Very slow | Close other host apps. Do not run Virtuoso and big simulations at the same time. Check `top` in the guest. |
| Disk full | The guest root is 33 GB and nearly full. Free space: `df -h /`. Clean `~/gpdk_run/out`, and the `ahdlSimDB` folder in your Virtuoso work folder (verify where it is). Do this before big runs. |
| `virtuoso` cannot find a library | Check that you started it from the folder with `cds.lib`, and that the `DEFINE gpdk045` line is in it. |
| `vm/stop_vm.sh` says the VM is still running | A shutdown dialog may be open in the VM window, or a job is running. Shut down from inside the guest. Use `--force` only as a last resort: it can lose data. |
| `send_to_vm.sh` files not in `/media/TO_VM` | Run `ls /media` in the guest. If it is not there, run `sudo mount /dev/sr0 /mnt` (verify device name). |

## 9. What NOT to do

- Do **not** delete the `pristine` snapshot. It is the clean baseline.
- Do **not** run the VM, or Virtuoso, from the pen drive. It is slow and can
  corrupt the VM. Use `/home/parshu/vm/`.
- Do **not** detach or delete `/home/parshu/vm/scratch.vdi` while the VM
  uses it. Do **not** run `dd` on `/dev/sda` in the guest. `/dev/sda` is the
  system disk. Only `/dev/sdb` is the scratch disk.
- Do **not** power off the VM with the power button while a simulation is
  writing results. Stop the run first.
- Do **not** edit the VirtualBox files in `/home/parshu/vm/` by hand. Use
  VirtualBox or the `vm/` scripts.

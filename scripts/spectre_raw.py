#!/usr/bin/env python3
"""Convert a Spectre nutmeg ASCII raw file (`-format nutascii -raw ...`) into the table that
measure_tran.measure() reads: a whitespace table whose first line is

    time v(ck) v(q1) v(q2) v(q3) v(q4) v(q1b) v(q2b) v(q3b) v(q4b) i(vdd)

resampled onto a uniform time grid (np.interp). Spectre's VDD:p (current into the supply
probe) is written as i(vdd) with its sign unchanged, so supply current stays negative when the
source delivers power.

Usage: spectre_raw.py IN.raw|DIR OUT.txt [step_ps=5]
A directory argument is searched for the first *.raw file, then for a file named like "tran".
"""
import os
import re
import sys
import numpy as np

COLUMNS = ["time", "v(ck)", "v(q1)", "v(q2)", "v(q3)", "v(q4)",
           "v(q1b)", "v(q2b)", "v(q3b)", "v(q4b)", "i(vdd)"]
NODES = {"ck", "q1", "q2", "q3", "q4", "q1b", "q2b", "q3b", "q4b"}


def canonical(name):
    """Map a Spectre/nutmeg variable name onto one of COLUMNS, or None if not needed."""
    n = name.strip().lower()
    if n == "time":
        return "time"
    m = re.fullmatch(r"v\((.+)\)", n)
    base = m.group(1) if m else n
    if base in NODES:
        return f"v({base})"
    if base in ("vdd:p", "vdd", "i(vdd:p)", "i(vdd)") or n in ("i(vdd:p)", "i(vdd)"):
        return "i(vdd)"
    return None


def find_raw(path):
    """Resolve a raw file, or a directory holding one."""
    if os.path.isdir(path):
        names = sorted(os.listdir(path))
        for nm in names:
            if nm.endswith(".raw"):
                return os.path.join(path, nm)
        for nm in names:
            if "tran" in nm.lower() and os.path.isfile(os.path.join(path, nm)):
                return os.path.join(path, nm)
        raise FileNotFoundError(f"no .raw or tran* file in directory {path}")
    return path


def _parse_plot(lines):
    """Parse one plot block (list of lines starting at Title:). Returns (header dict, names, data)."""
    hdr, names, i = {}, [], 0
    while i < len(lines) and lines[i].strip() != "Values:" and lines[i].strip() != "Values":
        line = lines[i]
        if line.startswith("Variables:"):
            # Spectre puts the first variable (time) on the same line as "Variables:"
            rest = line[len("Variables:"):].split()
            if len(rest) >= 2 and rest[0].isdigit():
                names.append(rest[1])
            i += 1
            while i < len(lines) and re.match(r"^\s*\d+\s+\S+", lines[i]):
                parts = lines[i].split()
                names.append(parts[1])
                i += 1
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            hdr[k.strip()] = v.strip()
        i += 1
    if i >= len(lines):
        raise ValueError("raw plot has no Values: section")
    nvar = int(hdr.get("No. Variables", len(names)))
    npts = int(hdr.get("No. Points", "0"))
    if nvar != len(names):
        raise ValueError(f"declared {nvar} variables, listed {len(names)}")
    if hdr.get("Flags", "real").lower().startswith("complex"):
        raise ValueError("complex raw data is not supported")
    # Values: per point an index token followed by one value per variable (the index line
    # carries the first value). Read as a token stream so line layout does not matter.
    toks = " ".join(lines[i + 1:]).split()
    stride = nvar + 1
    if npts and len(toks) < npts * stride:
        raise ValueError(f"expected {npts} points, found {len(toks)//stride}")
    arr = np.array(toks[: (len(toks) // stride) * stride], dtype=float).reshape(-1, stride)
    return hdr, names, arr[:, 1:]


def read_tran(raw_path):
    """Return {canonical column: samples} for the transient plot of a nutascii raw file."""
    with open(raw_path, errors="replace") as f:
        text = f.read().splitlines()
    starts = [k for k, l in enumerate(text) if l.startswith("Title:")]
    if not starts:
        raise ValueError(f"{raw_path}: not a nutmeg raw file (no Title: line)")
    starts.append(len(text))
    chosen = None
    for a, b in zip(starts[:-1], starts[1:]):
        block = text[a:b]
        plot = next((l.split(":", 1)[1].strip() for l in block if l.startswith("Plotname:")), "")
        if re.search(r"tran", plot, re.I):
            chosen = block
            break
    if chosen is None:
        chosen = text[starts[0]:starts[1]]
    hdr, names, data = _parse_plot(chosen)
    cols = {}
    for j, nm in enumerate(names):
        c = canonical(nm)
        if c and c not in cols:
            cols[c] = data[:, j]
    missing = [c for c in COLUMNS if c not in cols]
    if missing:
        raise ValueError(f"{raw_path}: missing signals {missing}; variables were {names}")
    return cols


def convert(raw_path, out_path, step_s=5e-12):
    """Write the measure_tran table for the transient in raw_path. Returns the output path."""
    raw_path = find_raw(raw_path)
    cols = read_tran(raw_path)
    t = cols["time"]
    order = np.argsort(t, kind="stable")
    t = t[order]
    grid = np.arange(t[0], t[-1], step_s)
    out = np.column_stack([grid] + [np.interp(grid, t, cols[c][order]) for c in COLUMNS[1:]])
    with open(out_path, "w") as f:
        f.write(" ".join(COLUMNS) + "\n")
        np.savetxt(f, out, fmt="%.9e")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    step = float(sys.argv[3]) * 1e-12 if len(sys.argv) > 3 else 5e-12
    convert(sys.argv[1], sys.argv[2], step)
    print(f"wrote {sys.argv[2]}")

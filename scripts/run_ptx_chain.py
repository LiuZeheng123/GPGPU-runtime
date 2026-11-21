"""Run vadd followed by affine on the same device allocation, using a simulator."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from ptx_launch import BufferSlice
from ptx_runtime import Context


MASK = 0xffffffff
BLOCK = 32
OFFSET = 2  # Leave two guard words before each active slice.


def pack(words):
    return struct.pack("<%dI" % len(words), *words)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def launch_stage(ctx, module_dir, handles, count, scalars):
    module = ctx.load(module_dir)
    params = [BufferSlice(handle, OFFSET * 4, count * 4, access)
              for handle, access in zip(handles, ("r", "r", "w"))]
    grid = (max(1, (count + BLOCK - 1) // BLOCK), 1, 1)
    event = ctx.launch(module, module.manifest["entry"], grid, (BLOCK, 1, 1),
                       params + [count] + scalars)
    completion = ctx.wait(event)
    ctx.unload(module)
    return completion


def run_case(ctx, modules, count, alpha):
    size = OFFSET + count + 3
    x = [(MASK - 7 * i) & MASK for i in range(size)]
    y = [(0x80000007 + 11 * i) & MASK for i in range(size)]
    temporary = [0xdeadbeef] * size
    output = [0xa5a5a5a5] * size
    initial = [x, y, temporary, output]
    handles = [ctx.alloc(size * 4) for _ in initial]
    for handle, values in zip(handles, initial):
        ctx.write(handle, 0, pack(values))

    x_buf, y_buf, temp_buf, out_buf = handles
    first = launch_stage(ctx, modules / "vadd", [x_buf, y_buf, temp_buf], count, [])
    second = launch_stage(ctx, modules / "affine", [temp_buf, y_buf, out_buf], count, [alpha])

    # Read back only after both kernels have completed.
    expected = [values.copy() for values in initial]
    for i in range(OFFSET, OFFSET + count):
        expected[2][i] = (x[i] + y[i]) & MASK
        expected[3][i] = (alpha * (x[i] + y[i]) + y[i]) & MASK
    observed = {}
    for name, handle, answer in zip(("x", "y", "temporary", "output"), handles, expected):
        raw = ctx.read(handle, 0, size * 4)
        values = list(struct.unpack("<%dI" % size, raw))
        if values != answer:
            index = next(i for i in range(size) if values[i] != answer[i])
            raise ValueError("n=%d %s[%d]: expected %08x, got %08x" %
                             (count, name, index, answer[index], values[index]))
        observed[name] = values
    for handle in handles:
        ctx.free(handle)
    return dict(n=count, alpha=alpha, offset_words=OFFSET, completions=[first, second],
                observed=observed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=["simx", "rtlsim", "xrtsim"], required=True)
    for name in ("modules", "binding", "target-lock", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    # Refuse to overwrite a previous run.
    with args.output.open("x", encoding="utf-8") as report:
        result = dict(status="FAIL", backend=args.backend, cases=[], argv=sys.argv[1:])
        ctx = None
        try:
            result["sha256"] = {
                "binding": digest(args.binding), "target_lock": digest(args.target_lock),
                "runtime": digest(Path(__file__).with_name("ptx_runtime.py")),
                "example": digest(Path(__file__)),
                "images": {name: digest(args.modules / name / "kernel.vxbin")
                           for name in ("vadd", "affine")}}
            ctx = Context(args.binding, args.target_lock, backend=args.backend,
                          run_id=args.output.stem)
            result["caps"] = ctx.query_caps()
            for count, alpha in [(0, 3), (1, 3), (32, 7), (33, MASK), (65, 3)]:
                result["cases"].append(run_case(ctx, args.modules, count, alpha))
            ctx.close()
            result["status"] = "PASS"
        except Exception as exc:
            result["error"] = repr(exc)
            if ctx is not None and ctx.state == "READY":
                try:
                    ctx.close()
                except Exception as close_error:
                    result["close_error"] = repr(close_error)
        json.dump(result, report, indent=2)
        report.write("\n")
    print(args.backend, result["status"], len(result["cases"]), result.get("error", ""))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

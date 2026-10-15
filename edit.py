#!/usr/bin/env python3
"""Device showcase edit: vertical 1080x1920, 30fps, no text, no audio (music added later).

Usage: python3 edit.py <proxy_dir> <work_dir> <out.mp4>
Proxies are 1080x1920 SDR versions of the original clips (see README.md).
"""
import os
import subprocess
import sys

PROX, WORK, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
FPS = 30
os.makedirs(WORK, exist_ok=True)

GRADE = ("eq=contrast=1.08:saturation=1.28:gamma=1.0,"
         "colorbalance=rm=-0.03:gm=0.02:bm=-0.02:rh=0.02:bh=-0.03,"
         "unsharp=5:5:0.5,vignette=PI/6")

# (file, src_in, src_out, speed-or-ramp, zoom, motion_blur_frames, transition_into_next)
# speed: number, or list of (src_until, speed) pieces for speed ramps.
# transition: "cut" or (xfade_name, duration)
P1 = "IMG_99{}.mp4"
V42 = "VID20261015160442.mp4"
V06 = "VID20261015160506.mp4"

SEGS = [
    # --- Part 1: devices on display ---
    (P1.format(77), 0.0, 3.0, 1.4, 0.07, 0, ("zoomin", 0.35)),
    (P1.format(78), 0.5, 3.5, [(1.3, 3.0), (3.5, 1.1)], 0.06, 0, ("smoothup", 0.30)),
    (P1.format(79), 0.0, 4.0, 1.8, 0.10, 0, ("fadewhite", 0.30)),
    (P1.format(81), 0.0, 3.4, 1.5, 0.06, 0, ("slideleft", 0.25)),
    (P1.format(82), 1.0, 8.5, 3.5, 0.04, 3, ("circleopen", 0.35)),
    (P1.format(83), 0.0, 5.0, 2.2, 0.06, 0, ("hblur", 0.30)),
    (P1.format(84), 0.0, 5.9, 2.6, 0.05, 0, ("wipeup", 0.25)),
    (P1.format(86), 0.0, 5.7, 2.5, 0.06, 0, ("smoothleft", 0.30)),
    (P1.format(87), 0.0, 2.6, 2.0, 0.08, 0, ("squeezev", 0.20)),
    (P1.format(88), 0.0, 2.58, 2.0, 0.08, 0, ("zoomin", 0.20)),
    (P1.format(89), 0.0, 4.4, 3.3, 0.08, 0, ("fadewhite", 0.40)),
    # --- Part 2: store + devices in hand ---
    (V42, 5.0, 11.0, 2.5, 0.05, 2, ("zoomin", 0.30)),
    (V42, 0.3, 3.9, 1.6, 0.05, 0, "cut"),
    (V42, 12.0, 15.9, 1.7, 0.05, 0, "cut"),
    (V06, 0.0, 3.8, 1.7, 0.05, 0, "cut"),
    (V06, 4.0, 7.8, 12.0, 0.0, 10, "cut"),    # whip through the store
    (V06, 7.8, 12.6, 2.2, 0.05, 0, "cut"),
    (V06, 12.8, 16.8, 12.0, 0.0, 10, "cut"),
    (V06, 16.8, 21.6, 2.2, 0.05, 0, "cut"),
    (V06, 22.0, 31.8, 25.0, 0.0, 12, "cut"),
    (V06, 31.8, 35.8, 1.8, 0.05, 0, "cut"),
    (V06, 36.0, 41.8, 15.0, 0.0, 10, "cut"),
    (V06, 41.8, 45.8, 1.8, 0.05, 0, "cut"),
    (V06, 46.0, 53.8, 20.0, 0.0, 12, "cut"),
    (V06, 53.8, 58.6, 2.2, 0.05, 0, "cut"),
    (V06, 58.8, 63.8, 13.0, 0.0, 10, "cut"),
    (V06, 63.8, 67.8, 1.6, 0.06, 0, None),
]


def ramp(src_in, src_out, speed):
    """setpts expression and output duration for a constant or piecewise speed."""
    pieces = speed if isinstance(speed, list) else [(src_out, speed)]
    expr, acc, prev = None, 0.0, src_in
    terms = []
    for until, s in pieces:
        terms.append((prev - src_in, until - src_in, acc, s))
        acc += (until - prev) / s
        prev = until
    expr = f"{terms[-1][2]}+(T-{terms[-1][0]})/{terms[-1][3]}"
    for a, b, base, s in reversed(terms[:-1]):
        expr = f"if(lt(T,{b}),{base}+(T-{a})/{s},{expr})"
    return expr, acc


def render_segment(i, seg):
    f, a, b, speed, zoom, blur, _ = seg
    expr, dur = ramp(a, b, speed)
    out = os.path.join(WORK, f"seg{i:02d}.mp4")
    vf = [f"setpts='({expr})/TB'"]
    if blur:
        vf.append(f"tmix=frames={blur}")
    vf.append(f"fps={FPS}")
    if zoom:
        vf.append(f"scale=w='2*trunc(540*(1+{zoom}*t/{dur:.3f}))':h=-2:eval=frame:flags=bicubic")
        vf.append("crop=1080:1920")
    vf.append(GRADE)
    vf.append("format=yuv420p")
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", str(a), "-t", str(b - a),
           "-i", os.path.join(PROX, f), "-vf", ",".join(vf), "-an",
           "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-r", str(FPS), out]
    return cmd, out


def probe(path):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]))


def main():
    procs, outs = [], []
    for i, seg in enumerate(SEGS):
        cmd, out = render_segment(i, seg)
        outs.append(out)
        if os.path.exists(out) and "--fresh" not in sys.argv:
            continue
        procs.append(subprocess.Popen(cmd))
        if len(procs) >= 4:
            procs.pop(0).wait()
    for p in procs:
        p.wait()
    durs = [probe(o) for o in outs]

    inputs, graph = [], []
    for o in outs:
        inputs += ["-i", o]
    cur, curdur = "[0:v]", durs[0]
    flashes = []
    for i in range(1, len(outs)):
        tr = SEGS[i - 1][6]
        lab = f"[v{i}]"
        if tr == "cut":
            graph.append(f"{cur}[{i}:v]concat=n=2:v=1:a=0{lab}")
            curdur += durs[i]
        else:
            name, d = tr
            off = curdur - d
            graph.append(f"{cur}[{i}:v]xfade=transition={name}:duration={d}:offset={off:.3f}{lab}")
            if name in ("zoomin", "circleopen", "smoothup"):
                flashes.append(off + d / 2)
            curdur += durs[i] - d
        cur = lab
    total = curdur
    # warm light-leak passes at the opening and on flashier transitions
    leaks = [0.4] + flashes
    env = "+".join(f"exp(-pow((T-{t:.2f})/0.3,2))" for t in leaks)
    leak = (f"color=c=black:s=270x480:r={FPS}:d={total:.3f},format=rgb24,"
            f"geq=r='150*({env})*exp(-(pow(X-W*(0.2+0.6*mod(T,1.7)/1.7),2)+pow(Y-H*0.35,2))/(2*pow(W*0.45,2)))':"
            f"g='85*({env})*exp(-(pow(X-W*(0.2+0.6*mod(T,1.7)/1.7),2)+pow(Y-H*0.35,2))/(2*pow(W*0.45,2)))':"
            f"b='30*({env})*exp(-(pow(X-W*(0.2+0.6*mod(T,1.7)/1.7),2)+pow(Y-H*0.35,2))/(2*pow(W*0.45,2)))',"
            "scale=1080:1920:flags=bicubic,gblur=sigma=20,format=gbrp[leak]")
    graph.append(leak)
    graph.append(f"{cur}format=gbrp[base]")
    graph.append("[base][leak]blend=all_mode=screen,"
                 "noise=alls=5:allf=t,"
                 f"fade=t=in:st=0:d=0.3,fade=t=out:st={total - 0.6:.3f}:d=0.6,format=yuv420p[out]")
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y", *inputs,
           "-filter_complex", ";".join(graph), "-map", "[out]",
           "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high",
           "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart", OUT]
    subprocess.check_call(cmd)
    print(f"done: {OUT} ({total:.2f}s)")


if __name__ == "__main__":
    main()

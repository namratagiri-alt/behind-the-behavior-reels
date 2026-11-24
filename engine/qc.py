"""Automated QC for a rendered Reel: specs, loudness, black/frozen frames, contact sheet."""
import json, subprocess, sys, re, os
from PIL import Image

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def qc(outdir, rid):
    mp4 = f"{outdir}/{rid}.mp4"
    tl = json.load(open(f"{outdir}/{rid}_timeline.json"))
    probe = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", mp4]).stdout)
    v = [s for s in probe["streams"] if s["codec_type"] == "video"][0]
    a = [s for s in probe["streams"] if s["codec_type"] == "audio"][0]
    dur = float(probe["format"]["duration"]); size_mb = int(probe["format"]["size"]) / 1e6
    loud = run(["ffmpeg", "-hide_banner", "-i", mp4, "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", loud)[-1]); TP = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", loud)[-1])
    blk = run(["ffmpeg", "-hide_banner", "-i", mp4, "-vf", "blackdetect=d=0.3:pix_th=0.05", "-an", "-f", "null", "-"]).stderr
    blacks = re.findall(r"black_start:([\d.]+)", blk)
    checks = {
        "resolution_1080x1920": (v["width"], v["height"]) == (1080, 1920),
        "codec_h264_yuv420p": v["codec_name"] == "h264" and v["pix_fmt"] == "yuv420p",
        "fps_30": v["r_frame_rate"] == "30/1",
        "audio_aac_48k": a["codec_name"] == "aac" and a["sample_rate"] == "48000",
        "duration_30_to_45s": 30 <= dur <= 45.5,
        "size_under_100MB": size_mb < 100,
        "no_black_segments": len(blacks) == 0,
        "loudness_-18_to_-11_LUFS": -18 <= I <= -11,
        "true_peak_below_-0.5dB": TP < -0.5,
        "cover_exists": os.path.exists(f"{outdir}/{rid}_cover.jpg"),
        "srt_exists": os.path.exists(f"{outdir}/{rid}.srt"),
    }
    # structure: hook 0-3 s, setup to ~15 s, proof 15-25 s, takeaway last 5-8 s
    sc = tl["scenes"]; roles = [x.get("role") for x in sc]
    hooks = [x for x in sc if x.get("role") == "hook"]
    setup = [x for x in sc if x.get("role") == "setup"]
    proof = [x for x in sc if x.get("role") == "proof"]
    last = sc[-1]
    checks.update({
        "structure_roles_in_order": roles == sorted(roles, key=lambda r: ["hook", "setup", "proof", "takeaway"].index(r) if r in ("hook", "setup", "proof", "takeaway") else 9) and set(roles) >= {"hook", "setup", "proof", "takeaway"},
        "hook_voice_within_2s": bool(hooks) and hooks[-1]["voice_end"] <= 2.4,
        "hook_has_on_screen_text": bool(hooks) and all(h["on_screen_text"] for h in hooks),
        "setup_ends_by_16s": bool(setup) and 10 <= setup[-1]["end"] <= 16.5,
        "proof_covers_15_to_25s": bool(proof) and proof[0]["start"] <= 16.5 and proof[-1]["end"] >= 24,
        "illustrated_half_of_scenes": sum(1 for x in sc if x.get("illustration")) * 2 >= len(sc),
        "max_2_headline_scenes": sum(1 for x in sc if x["type"] == "headline") <= 2,
        "takeaway_last_5_to_8s": last.get("role") == "takeaway" and 5 <= (last["end"] - last["start"]) <= 8.5,
    })
    # contact sheet: midpoint and late point of each scene
    times = []
    for s in tl["scenes"]:
        times += [s["start"] + (s["end"] - s["start"]) * 0.75]
    frames = []
    for i, t in enumerate(times):
        p = f"/tmp/{rid}_{i}.png"
        run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t:.2f}", "-i", mp4, "-frames:v", "1", "-vf", "scale=270:480", p])
        frames.append(Image.open(p))
    sheet = Image.new("RGB", (270 * len(frames), 480))
    for i, f in enumerate(frames): sheet.paste(f, (i * 270, 0))
    sheet.save(f"{outdir}/{rid}_contact.png")
    report = {"id": rid, "duration_s": round(dur, 2), "size_mb": round(size_mb, 2), "integrated_lufs": I,
              "true_peak_dbfs": TP, "checks": checks,
              "auto_pass": all(checks.values())}
    json.dump(report, open(f"{outdir}/{rid}_qc.json", "w"), indent=1)
    return report

if __name__ == "__main__":
    print(json.dumps(qc(sys.argv[1], sys.argv[2]), indent=1))

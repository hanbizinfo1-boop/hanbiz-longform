# -*- coding: utf-8 -*-
r"""확정본 + 얹을 것(카드·강조·효과음)을 합성한 «완성 미리보기» — 한 구간, 720p 확인용.

    python final_preview.py <map.json> <얹을것.xml> <카메라.MP4> <녹화.mp4> <녹화offset> <시작초> <끝초> <출력.mp4>

사장님 시퀀스를 재현: 자료 구간 = 녹화 전체 + 원형 PIP(중심 126,956 · 반지름 154) / 인물 구간 = 카메라 전체.
그 위에 XML 의 카드 영상·강조 PNG, 소리 = 카메라 소리 + 효과음.  자막은 넣지 않는다.
"""

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote

from PIL import Image, ImageDraw

FPS = 60000 / 1001
S = 2 / 3                     # 1080 → 720
SRC_C, SRC_R = (1682, 1092), 732
OUT_C, OUT_R = (126, 956), 154


def main():
    m = json.load(open(sys.argv[1], encoding="utf-8"))
    seq = ET.parse(sys.argv[2]).getroot().find("sequence")
    cam, rec, off = sys.argv[3], sys.argv[4], float(sys.argv[5])
    T0, T1, out = float(sys.argv[6]), float(sys.argv[7]), Path(sys.argv[8])
    parts = []
    for t0, t1, s0, s1 in m["pieces"]:
        x, y = max(T0, t0), min(T1, t1)
        if y - x > 1e-3:
            parts.append((s0 + (x - t0), s0 + (y - t0)))
    ss = max(parts[0][0] - 1, 0)
    span = parts[-1][1] - ss + 1
    sel_c = "+".join(f"between(t,{a - ss:.4f},{b - ss:.4f})" for a, b in parts)
    rss = max(ss - off, 0)
    sel_r = "+".join(f"between(t,{a - off - rss:.4f},{b - off - rss:.4f})" for a, b in parts)
    dur = T1 - T0
    modes = [(max(a, T0) - T0, min(b, T1) - T0) for a, b, k in m["modes"] if k == "자료" and b > T0 and a < T1]
    en_pip = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in modes) or "0"
    en_cam = f"not({en_pip})"

    d = int(OUT_R * 2 * S)
    mask = out.with_suffix(".mask.png")
    mk = Image.new("L", (d * 4, d * 4), 0)
    ImageDraw.Draw(mk).ellipse((0, 0, d * 4 - 1, d * 4 - 1), fill=255)
    mk.resize((d, d), Image.LANCZOS).save(mask)

    ins = ["-ss", f"{ss:.3f}", "-t", f"{span:.3f}", "-i", cam,
           "-ss", f"{rss:.3f}", "-t", f"{span:.3f}", "-i", rec, "-loop", "1", "-i", str(mask)]
    f = [f"[0:v]select='{sel_c}',setpts=N/FRAME_RATE/TB,split=2[c1][c2]",
         "[c1]scale=1280:720[camf]",
         f"[c2]crop={SRC_R * 2}:{SRC_R * 2}:{SRC_C[0] - SRC_R}:{SRC_C[1] - SRC_R},scale={d}:{d},format=yuva420p[cp]",
         "[2:v]format=gray[mk]", "[cp][mk]alphamerge[pip]",
         f"[1:v]select='{sel_r}',setpts=N/FRAME_RATE/TB,fps=60000/1001,scale=1280:720[rec]",
         f"[rec][pip]overlay={int((OUT_C[0] - OUT_R) * S)}:{int((OUT_C[1] - OUT_R) * S)}:enable='{en_pip}'[b1]",
         f"[b1][camf]overlay=0:0:enable='{en_cam}'[b2]"]
    cur, k = "b2", 3
    # 카드·강조 (비디오 트랙 순서대로 위로)
    for tr in seq.findall("./media/video/track"):
        for c in tr.findall("clipitem"):
            a, b = int(c.findtext("start")) / FPS - T0, int(c.findtext("end")) / FPS - T0
            if b <= 0 or a >= dur:
                continue
            fid = c.find("file")
            pu = fid.findtext("pathurl") or seq.find(f".//file[@id='{fid.get('id')}']").findtext("pathurl")
            p = unquote(pu.replace("file://localhost/", ""))
            if p.lower().endswith(".png"):
                ins += ["-loop", "1", "-t", f"{dur:.3f}", "-i", p]
                f.append(f"[{k}:v]scale=1280:720[o{k}]")
            else:
                ins += ["-itsoffset", f"{max(a, 0):.3f}", "-ss", f"{max(-a, 0):.3f}", "-i", p]
                f.append(f"[{k}:v]scale=1280:720,setpts=PTS[o{k}]")
            f.append(f"[{cur}][o{k}]overlay=0:0:eof_action=pass:enable='between(t,{a:.3f},{b:.3f})'[x{k}]")
            cur, k = f"x{k}", k + 1
    f.append(f"[{cur}]trim=duration={dur:.3f},format=yuv420p[vout]")
    # 소리
    f.append(f"[0:a]aselect='{sel_c}',asetpts=N/SR/TB[voice]")
    amix = ["[voice]"]
    for tr in seq.findall("./media/audio/track"):
        for c in tr.findall("clipitem"):
            a = int(c.findtext("start")) / FPS - T0
            if a < 0 or a >= dur:
                continue
            fid = c.find("file")
            pu = fid.findtext("pathurl") or seq.find(f".//file[@id='{fid.get('id')}']").findtext("pathurl")
            ins += ["-i", unquote(pu.replace("file://localhost/", ""))]
            f.append(f"[{k}:a]adelay={int(a * 1000)}|{int(a * 1000)}[s{k}]")
            amix.append(f"[s{k}]")
            k += 1
    f.append("".join(amix) + f"amix=inputs={len(amix)}:normalize=0,atrim=duration={dur:.3f}[aout]")
    script = out.with_suffix(".filter.txt")
    script.write_text(";".join(f), encoding="utf-8")
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex_script", str(script),
                    "-map", "[vout]", "-map", "[aout]", "-c:v", "h264_nvenc", "-cq", "24",
                    "-c:a", "aac", "-b:a", "192k", str(out)], check=True)
    script.unlink()
    mask.unlink()
    print(f"저장: {out}")


if __name__ == "__main__":
    sys.exit(main())

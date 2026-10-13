# -*- coding: utf-8 -*-
r"""제작 컴퓨터 «분석» 단계 — 원문 한 편 → 핸드오프/<건>/10_분석/ (기획이 연출표를 짜는 재료).

    python tools/auto/analyze.py <건 폴더> --mp4 <원문.mp4> --prproj <저장본.prproj> --seq "<시퀀스 이름>" --media "<원본 폴더>"

만드는 것(실명은 넣지 않는다 — 화면색인·모자이크후보는 OCR 글자 중 금지어·번호를 ○○ 로)
  층.md          트랙 수 · 사람 PIP(모션 값) · 모션 없는 V2(사람 전체 화면 컷) 시각 · 시작/끝 영상
  자막.txt       «번호 시작초 끝초 글»(prproj C1 — 글 블롭을 못 읽은 줄은 «(빈)»)
  받아쓰기.txt   whisper 문장 «시작초 끝초 글»
  자막검수.md    sub_diff(받아쓰기와 다른 곳) · sub_timing(강제 정렬 판정 요약)
  화면색인.md    10초마다 화면 종류(관리 화면 메뉴/텔레그램/카메라 전체)와 OCR 핵심 글자 몇 개
  모자이크후보.md 텔레그램 창 구간 · 금지어 칸이 보이는 시각(글자는 ○○)
  화면모음/      10초 간격 모음(장당 12컷, 640px, 시각 표시)
중간 파일(큰 것)은 _tmp/<건>/ (git 제외).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable


def run(*a):
    print("  $", " ".join(str(x) for x in a), flush=True)
    subprocess.run([str(x) for x in a], check=True, env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job"); ap.add_argument("--mp4", required=True); ap.add_argument("--prproj", required=True)
    ap.add_argument("--seq", required=True); ap.add_argument("--media", required=True)
    a = ap.parse_args()
    job = Path(a.job); out = job / "10_분석"; out.mkdir(parents=True, exist_ok=True)
    tmp = ROOT / "_tmp" / job.name; tmp.mkdir(parents=True, exist_ok=True)
    edit = tmp / "edit.json"
    import shutil
    shutil.copy(a.prproj, tmp / "src.prproj")
    run(PY, ROOT / "tools/read_lecture_edit.py", tmp / "src.prproj", a.seq, edit)
    items = json.load(open(edit, encoding="utf-8"))["items"]
    # 층
    from collections import Counter
    v2 = [i for i in items if i["track"] == "V2"]
    full = [i for i in v2 if not any(f.get("name") == "모션" for f in i.get("fx", []))]
    mot = Counter(json.dumps(next((f["params"] for f in i["fx"] if f.get("name") == "모션"), {}), ensure_ascii=False)[:120] for i in v2)
    L = [f"# 층 — {a.seq}", "", f"- 트랙: {dict(Counter(i['track'] for i in items))}",
         f"- 사람(V2) 모션 값(상위): {mot.most_common(3)}",
         f"- 모션 없는 V2(사람 전체 화면 컷): {[(round(i['t0'], 2), round(i['t1'], 2)) for i in full]}",
         f"- 소스: {dict(Counter(i.get('name') for i in items if i['track'] in ('V1', 'V2')))}"]
    (out / "층.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    caps = sorted((i for i in items if i["track"] == "C1"), key=lambda i: i["t0"])
    (out / "자막.txt").write_text("\n".join(f"{k}\t{c['t0']:.3f}\t{c['t1']:.3f}\t{c.get('text') or '(빈)'}" for k, c in enumerate(caps)) + "\n", encoding="utf-8")
    # 받아쓰기
    wav = tmp / "a16k.wav"
    run("ffmpeg", "-v", "error", "-y", "-i", a.mp4, "-vn", "-ac", "1", "-ar", "16000", wav)
    words = tmp / "words.json"
    if not words.exists():
        run(PY, ROOT / "tools/transcribe_words.py", wav, words)
    segs = json.load(open(words, encoding="utf-8"))
    (out / "받아쓰기.txt").write_text("\n".join(f"{s['t0']:.2f}\t{s['t1']:.2f}\t{s['text']}" for s in segs) + "\n", encoding="utf-8")
    # 자막 검수
    run(PY, ROOT / "tools/auto/sub_diff.py", edit, words, tmp / "subdiff.md")
    run(PY, ROOT / "tools/auto/sub_timing.py", edit, wav, tmp / "subtiming.json")
    tm = json.load(open(tmp / "subtiming.json", encoding="utf-8"))
    bad = [r for r in tm if r.get("verdict", ["판단불가"]) != ["맞음"]]
    (out / "자막검수.md").write_text("# 자막 검수 후보(제작 분석 — 판정은 기획)\n\n## 받아쓰기와 다른 곳\n\n" +
                                   (tmp / "subdiff.md").read_text(encoding="utf-8").split("\n", 2)[2] +
                                   "\n## 강제 정렬 판정이 «맞음»이 아닌 줄\n\n" +
                                   "\n".join(f"- {r['t0']:.2f} {r.get('verdict')} lag {r.get('lag')} tail {r.get('tail')} 점수 {r.get('score')} «{r['text']}»" for r in bad) + "\n",
                                   encoding="utf-8")
    # OCR (녹화 소스)
    rec = next((i["name"] for i in items if i["track"] == "V1" and "화면" in i.get("name", "")), None)
    ocr = tmp / "ocr.json"
    if rec and not ocr.exists():
        run(PY, ROOT / "tools/mosaic_scan.py", edit, Path(a.media) / rec, ocr, "0.5")
    sys.path.insert(0, str(ROOT))
    from tools.auto import termhash
    fp = job / "00_금지어지문.json"                    # 기획이 실명 없이 넘긴 금지어 지문
    tdata = termhash.load(fp) if fp.exists() else None

    class _M:                                          # mask.search / mask.sub 자리
        def search(self, t):
            return tdata is not None and termhash.hit(t, tdata)

        def sub(self, rep, t):
            return rep if self.search(t) else t
    mask = _M()
    ph = re.compile(r"01[0-9][-. ]?\d{3,4}[-. ]?\d{4}")

    def clean(t):
        t = mask.sub("○○", t) if mask else t
        return ph.sub(lambda m: m.group(0)[:8] + "****" if not m.group(0).startswith(("010-0000", "010-0010")) else m.group(0), t)
    lines = ["# 화면 색인 (10초마다 — OCR 핵심 글자, 실명 ○○)", ""]
    v1 = [i for i in items if i["track"] == "V1" and i.get("name") == rec]
    if ocr.exists():
        d = json.load(open(ocr, encoding="utf-8"))
        for smp in d["samples"]:
            ts = [i["t0"] + smp["s"] - i["s0"] for i in v1 if i["s0"] <= smp["s"] < i["s1"]]
            if not ts or int(ts[0] * 2) % 20:
                continue
            big = sorted(smp["boxes"], key=lambda b: -(b[3] - b[1]))[:8]
            lines.append(f"- {ts[0]:7.1f}s: " + " · ".join(clean(b[4]) for b in big))
    (out / "화면색인.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "모자이크후보.md").write_text("# 모자이크 후보\n\n- 텔레그램·알림 팝업·금지어 칸은 제작 단계에서 `build_mosaic` 방식으로 다시 잡는다(10-13 파트너센터 본보기).\n"
                                    "- 기획이 연출표에서 «이 구간 모자이크 + 예시 카드»를 정할 때 화면색인의 텔레그램 구간을 본다.\n", encoding="utf-8")
    # 화면 모음 — 개인정보 가림
    import numpy as np
    smp_by = []
    if ocr.exists():
        for smp in json.load(open(ocr, encoding="utf-8"))["samples"]:
            for i in v1:
                if i["s0"] <= smp["s"] < i["s1"]:
                    smp_by.append((i["t0"] + smp["s"] - i["s0"], smp["boxes"]))
        smp_by.sort()

    def privacy_mask(im, t):
        arr = np.array(im.convert("RGB")); h, w = arr.shape[:2]; k = w / 1920
        roi = arr[int(150 * k):int(900 * k), int(500 * k):int(1400 * k)].astype(int)
        r_, g_, b_ = roi[..., 0], roi[..., 1], roi[..., 2]
        if ((g_ > r_ + 4) & (g_ > b_ + 12) & (g_ > 150) & (g_ < 235)).mean() > 0.25:      # 텔레그램 대화 바탕
            return im.resize((w // 24, h // 24)).resize((w, h), Image.NEAREST)
        near = [bx for tt, bx in smp_by if abs(tt - t) < 0.6]
        for bxs in near[:1]:
            for b in bxs:
                txt = b[4].replace(" ", "")
                if (mask and mask.search(txt)) or (ph.search(txt) and not txt.startswith(("010-0000", "010-0010"))):
                    x0, y0, x1, y1 = [int(v * k) for v in b[:4]]
                    sub = im.crop((x0, y0, x1 + 1, y1 + 1)); im.paste(sub.resize((max(1, (x1 - x0) // 8), 1)).resize(sub.size), (x0, y0))
        return im

    # 화면 모음
    sh = out / "화면모음"; sh.mkdir(exist_ok=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.mp4], capture_output=True, text=True).stdout)
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 20)
    ts = list(range(5, int(dur), 10))
    for k in range(0, len(ts), 12):
        ims = []
        for t in ts[k:k + 12]:
            p = tmp / f"sh_{t}.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", a.mp4, "-frames:v", "1", "-vf", "scale=640:-1", str(p)])
            im = Image.open(p)
            im = privacy_mask(im, t)                         # 커밋되는 그림 — 텔레그램 통째·실제 번호·금지어 칸 가림(CLAUDE.md 4번)
            dr = ImageDraw.Draw(im); dr.rectangle((0, 0, 80, 26), fill=(0, 0, 0)); dr.text((4, 1), f"{t}s", font=f, fill=(255, 255, 0)); ims.append(im)
        o = Image.new("RGB", (1920, 360 * ((len(ims) + 2) // 3)))
        for i, im in enumerate(ims):
            o.paste(im, ((i % 3) * 640, (i // 3) * 360))
        o.save(sh / f"{ts[k]:04d}s.jpg", quality=70)
    print("분석 끝:", out)


if __name__ == "__main__":
    main()

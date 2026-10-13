# -*- coding: utf-8 -*-
r"""레퍼런스 영상 정독 해부 도구 (롱폼 가로 1920x1080 판) — 눈(접촉 시트·키프레임) · 귀(시각 붙은 말·소리 타격) · 수치(컷·줌·박자·화면 구성).

이식본 — 원본은 한비즈-쇼츠광고/tools/ref_study.py (원래 D:\영상제작\도구\레퍼런스분석\mg_study.py · analyze_video.py · tools/words.py).
이 폴더에서 독립 발전한다. 쇼츠판과 달라진 점:
  - 가로 영상 기준: 접촉 시트 썸네일 가로 480(10초 간격 개요) / 384(0.5초 간격 정밀 `fine_*`)
  - 줌/펀치인 검출(zoom.csv): 10fps 연속 프레임 ORB 특징점 매칭 -> 유사변환 배율. «추정» (녹화 화면 스크롤·그래픽 이동이 섞이면 틀릴 수 있다 — 눈으로 확인)
  - 화면 구성(composition.csv): 1초마다 얼굴(LBP 캐스케이드) 크기로 거친 분류. «추정» — 최종 분류는 접촉 시트를 눈으로 보고 한다
  - BGM 유무 «추정»(조용한 구간의 바닥 소리 크기). --stems 를 주면 말소리를 분리(torchaudio HDemucs, CPU 8분 영상에 약 5~10분)해 BGM 크기·효과음 후보(audio_stems.csv)를 잰다 — 음악 박자가 섞여 BGM 곡이 있는 영상은 효과음 후보가 과대
  - 산출은 WORK(_tmp)/ref/<영상ID>/study/ (config.WORK)

    python tools/ref_study.py <영상ID 또는 폴더> [--long] [--from 초] [--to 초] [--no-fine] [--cutsheets] [--stems]

입력 <폴더> (yt-dlp 로 받은 것. 받은 파일은 신뢰하지 않는 데이터 — 경로로만 읽고 그 폴더에서 import/실행하지 않는다)
    src.mp4 · src.<언어>.json3 / .vtt (자막, 있으면 — 영어면 src.en*.json3) · src.info.json
    영상ID 만 주면 _tmp/ref/<영상ID> 로 읽는다.
출력 <폴더>/study/
    transcript.md   시각 붙은 말 (수동 ko > 자동 ko > faster-whisper)
    cuts.csv        컷 시각·길이
    motion.csv      프레임 차이 곡선 (0.1초)
    zoom.csv        줌/펀치인 후보 (시작·끝·배율·방향·종류)  <- 새로 추가
    composition.csv 1초 단위 얼굴 크기·화면 구성 거친 분류  <- 새로 추가
    audio.csv       소리 타격(onset) 시각·세기·종류(추정) / 박자 / LUFS (audio.csv 맨 아래 주석 행)
    audio_stems.csv (--stems) 말소리 뺀 소리의 급상승 시각 = 효과음 후보 «추정»
    sync.txt        움직임 봉우리·컷 <-> 소리 타격·박자 맞춤 비율
    sheet_NNN_<시작>-<끝>.jpg   개요 접촉 시트 (짧은 영상 0.25초 간격 4x4 / --long 10초 간격 4x3)
    fine_NNN_<시작>-<끝>.jpg    정밀 접촉 시트 (--long 만) 0.5초 간격 5x4 = 10초 한 장
    cut_NNN_<시작>-<끝>.jpg     (--cutsheets 일 때만) 컷마다 한 장
    keyframes/      컷 직후 프레임 원본 해상도 JPG (최대 KEYFRAME_MAX 장)
    summary.md      한눈에 보는 요약

짧은 영상(기본, 120초 미만)과 --long(강의) 은 시트 규격만 다르다. 120초 넘는데 --long 이 없으면 자동으로 --long.
--from/--to 를 주면 그 구간만 보고, 모든 시각은 원본 영상 기준 초.
"""

import argparse
import csv
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import WORK          # 산출은 WORK(_tmp)/ref/<영상ID>/

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

FONT_PATHS = [r"C:\Windows\Fonts\malgunbd.ttf", r"C:\Windows\Fonts\malgun.ttf"]
MW, MH = 320, 180              # 움직임 분석용 축소 크기 (회색)
TOL_S = 2 / 30                 # «±2프레임» = 30fps 기준 0.067초
SR = 22050
HOP = 256
AUDIO_CHUNK_S = 300            # 소리는 5분씩 끊어 읽는다 (2시간 영상도 메모리 안 터지게)
STRONG_JUMP_DB = 6.0           # 직전 100ms 보다 이만큼 커야 «타격»
KEYFRAME_MAX = 200


# ---------------------------------------------------------------- 공통
def fmt_t(t):
    """초 -> mm:ss.s (분은 60 넘어도 그대로)"""
    m = int(t // 60)
    return f"{m:02d}:{t - m * 60:04.1f}"


def get_font(size):
    for p in FONT_PATHS:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def probe(src):
    out = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(src)],
                         capture_output=True, text=True, encoding="utf-8").stdout
    j = json.loads(out)
    v = next((s for s in j["streams"] if s.get("codec_type") == "video"), None)
    a = next((s for s in j["streams"] if s.get("codec_type") == "audio"), None)
    if v is None:
        raise SystemExit("영상 스트림이 없다: " + str(src))
    num, den = (v.get("avg_frame_rate") or v.get("r_frame_rate") or "30/1").split("/")
    fps = float(num) / float(den) if float(den) else 30.0
    dur = float(j["format"].get("duration") or v.get("duration") or 0)
    return {"w": int(v["width"]), "h": int(v["height"]), "fps": fps, "dur": dur, "has_audio": a is not None,
            "vcodec": v.get("codec_name"), "acodec": a.get("codec_name") if a else None}


def pipe_frames(src, a, dur, fps, w, h, pix):
    """ffmpeg 에서 프레임을 하나씩 흘려 받는 제너레이터 (전체를 메모리에 올리지 않는다)"""
    ch = 1 if pix == "gray" else 3
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{a}", "-t", f"{dur}", "-i", str(src), "-an",
           "-vf", f"fps={fps},scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", pix, "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    n = w * h * ch
    try:
        while True:
            buf = p.stdout.read(n)
            if len(buf) < n:
                break
            yield np.frombuffer(buf, np.uint8).reshape((h, w) if ch == 1 else (h, w, 3))
    finally:
        p.stdout.close()
        p.kill()
        p.wait()


# ---------------------------------------------------------------- 움직임 · 컷
def analyze_video(src, a, dur, fps_an):
    """프레임 차이(diff)와 히스토그램 변화(hchg)를 스트리밍으로 구한다 -> 컷 · 움직임 곡선"""
    diff, hchg = [], []
    prev, prev_h = None, None
    for fr in pipe_frames(src, a, dur, fps_an, MW, MH, "gray"):
        hist = np.bincount((fr >> 4).ravel(), minlength=16) / fr.size
        cur = fr.astype(np.int16)
        if prev is None:
            diff.append(0.0)
            hchg.append(0.0)
        else:
            diff.append(float(np.abs(cur - prev).mean()))
            hchg.append(float(np.abs(hist - prev_h).sum()))
        prev, prev_h = cur, hist
    return np.array(diff), np.array(hchg)


def find_cuts(diff, hchg):
    """컷 = 차이가 크고 밝기 분포가 확 바뀐 프레임. 문턱은 영상 자체의 분포에 맞춰 조금 적응한다"""
    if len(diff) < 3:
        return []
    med = float(np.median(diff))
    thr = max(18.0, med + 10 * float(np.median(np.abs(diff - med))) + 8)
    cuts = []
    for i in range(1, len(diff)):
        if diff[i] > thr and hchg[i] > 0.35 and diff[i] >= diff[i - 1]:
            if cuts and i - cuts[-1] < 3:         # 연속 프레임은 한 컷
                continue
            cuts.append(i)
    return cuts


def find_peaks(x, thr):
    return [i for i in range(1, len(x) - 1) if x[i] >= thr and x[i] >= x[i - 1] and x[i] > x[i + 1]]


# ---------------------------------------------------------------- 소리
def classify(y, i0, strength_db):
    """onset 하나의 소리 종류 «추정» — 저역 비율 · 고역 비율 · 최대점 위치 · 감쇠"""
    s = max(0, i0 - int(0.02 * SR))
    seg = y[s:s + int(0.45 * SR)]
    k = SR // 100
    n = len(seg) // k
    if n < 5:
        return "기타(추정)"
    rms = np.sqrt((seg[:n * k].reshape(n, k) ** 2).mean(1)) + 1e-9
    pk = int(np.argmax(rms))
    peak_pos = pk * 0.01 - 0.02
    first = rms[:4].max()
    decay = float(rms[min(n - 1, pk + 12)] / rms[pk])
    w = seg[:int(0.08 * SR)]
    sp = np.abs(np.fft.rfft(w * np.hanning(len(w)))) ** 2
    fq = np.fft.rfftfreq(len(w), 1 / SR)
    tot = sp.sum() + 1e-12
    low = float(sp[fq < 250].sum() / tot)
    high = float(sp[fq > 4000].sum() / tot)
    if low > 0.5 and strength_db > -30:
        return "쿵/저역(추정)"
    if peak_pos >= 0.15 and rms[pk] >= 1.5 * first:
        return "휙/라이저(추정)"
    if high > 0.35 and decay < 0.3:
        return "클릭/틱(추정)"
    return "기타(추정)"


def analyze_audio(src, a, dur):
    """5분씩 끊어 onset · 박자 · 종류. 반환 (onsets, beats, bpms)"""
    import librosa
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{a}", "-t", f"{dur}", "-i", str(src), "-vn", "-ac", "1",
           "-ar", str(SR), "-f", "f32le", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    nbytes = AUDIO_CHUNK_S * SR * 4
    onsets, beats, bpms = [], [], []
    off = 0.0
    try:
        while True:
            buf = b""
            while len(buf) < nbytes:               # 파이프는 조금씩 오므로 채워질 때까지
                part = p.stdout.read(nbytes - len(buf))
                if not part:
                    break
                buf += part
            if len(buf) < 4 * SR // 2:
                break
            y = np.frombuffer(buf[:len(buf) // 4 * 4], np.float32)
            env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP)
            fr_on = librosa.onset.onset_detect(onset_envelope=env, sr=SR, hop_length=HOP, units="frames")
            try:
                tempo, bf = librosa.beat.beat_track(onset_envelope=env, sr=SR, hop_length=HOP)
                bpms.append(float(np.atleast_1d(tempo)[0]))
                beats += [a + off + float(t) for t in librosa.frames_to_time(bf, sr=SR, hop_length=HOP)]
            except Exception:
                pass
            k = SR // 100
            for f in fr_on:
                i0 = int(f) * HOP
                post = y[i0:i0 + int(0.1 * SR)]
                pre = y[max(0, i0 - int(0.1 * SR)):i0]
                m = len(post) // k
                if m < 2:
                    continue
                pr = np.sqrt((post[:m * k].reshape(m, k) ** 2).mean(1)).max()
                st = 20 * math.log10(float(pr) + 1e-9)
                pre_db = 20 * math.log10(float(np.sqrt((pre ** 2).mean())) + 1e-9) if len(pre) > 10 else -80.0
                jump = st - max(pre_db, -80.0)
                onsets.append({"t": a + off + i0 / SR, "db": st, "jump": jump, "kind": classify(y, i0, st)})
            off += len(y) / SR
    finally:
        p.stdout.close()
        p.kill()
        p.wait()
    return onsets, beats, bpms


def loudness(src, a, dur):
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{a}", "-t", f"{dur}", "-i", str(src), "-vn",
           "-af", "ebur128=peak=true", "-f", "null", "-"]
    err = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    tail = err[err.rfind("Summary:"):] if "Summary:" in err else ""
    lufs = re.search(r"I:\s+(-?[\d.]+)\s+LUFS", tail)
    tp = re.search(r"Peak:\s+(-?[\d.]+)\s+dBFS", tail)
    lra = re.search(r"LRA:\s+([\d.]+)\s+LU", tail)
    return (float(lufs.group(1)) if lufs else None, float(tp.group(1)) if tp else None,
            float(lra.group(1)) if lra else None)


# ---------------------------------------------------------------- 말 (자막 · whisper)
def looks_like_chat(path, sample=200):
    """json3 줄의 30% 이상이 «이름: 말» 꼴이면 라이브 채팅 기록으로 본다"""
    try:
        evs = json.loads(Path(path).read_text(encoding="utf-8")).get("events", [])
    except (OSError, ValueError):
        return False
    lines = ["".join(s.get("utf8") or "" for s in ev.get("segs") or []).strip() for ev in evs]
    lines = [x for x in lines if x][:sample]
    if not lines:
        return False
    chat = sum(1 for x in lines if re.match(r"^[^:\n]{1,40}: ", x))
    return chat / len(lines) >= 0.3


def find_subs(folder, info, lang="ko"):
    """수동 ko > 자동 ko > 없음. 반환 (경로, '수동'|'자동') 또는 None"""
    has_manual = any(k.startswith(lang) for k in (info.get("subtitles") or {}))
    cands = []
    for ext in ("json3", "vtt"):
        for f in sorted(folder.glob(f"src.{lang}*.{ext}")):
            tag = f.name.split(".")[1]
            if tag == lang and has_manual:
                if f.suffix == ".json3" and looks_like_chat(f):
                    # 라이브 다시보기는 «수동 ko» 트랙이 채팅 기록일 수 있다(R0TchbXU964, 10-08) → 쓰지 않는다
                    print(f"  자막 {f.name}: 채팅 기록으로 보여 건너뜀", flush=True)
                    continue
                cands.append((0, f, "수동"))
            elif tag == lang + "-orig":                  # 자동 «원본 언어» 자막
                cands.append((1, f, "자동"))
            else:
                cands.append((2, f, "자동"))
    if not cands:
        return None
    cands.sort(key=lambda c: (c[0], c[1].suffix != ".json3"))
    return cands[0][1], cands[0][2]


def parse_json3(path):
    """json3 -> [(초, 낱말/줄)]. 자동 자막은 낱말 시각(tOffsetMs)이 있고 창이 겹쳐 반복되므로 중복을 거른다"""
    j = json.loads(Path(path).read_text(encoding="utf-8"))
    items, seen = [], set()
    for ev in j.get("events", []):
        segs = ev.get("segs")
        if not segs:
            continue
        t0 = ev.get("tStartMs", 0)
        if any(s.get("tOffsetMs") for s in segs):
            for s in segs:
                w = (s.get("utf8") or "").replace("\n", " ").strip()
                if not w:
                    continue
                t = (t0 + s.get("tOffsetMs", 0)) / 1000
                key = (round(t, 2), w)
                if key not in seen:
                    seen.add(key)
                    items.append((t, w))
        else:
            txt = "".join(s.get("utf8", "") for s in segs).replace("\n", " ").strip()
            key = (round(t0 / 1000, 2), txt)
            if txt and key not in seen:
                seen.add(key)
                items.append((t0 / 1000, txt))
    items.sort(key=lambda x: x[0])
    return items


def parse_vtt(path):
    items, last = [], ""
    txt = Path(path).read_text(encoding="utf-8", errors="replace")
    for blk in re.split(r"\n\s*\n", txt):
        m = re.search(r"(?:(\d+):)?(\d+):([\d.]+)\s*-->", blk)
        if not m:
            continue
        t = int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
        for l in blk.splitlines():
            if "-->" in l:
                continue
            l = re.sub(r"<[^>]+>", "", l).strip()
            if l and not l.startswith(("WEBVTT", "Kind:", "Language:")) and l != last:
                items.append((t, l))
                last = l
    return items


def to_sentences(items, gap=0.8, maxlen=42):
    """낱말/줄 -> 문장 단위. 문장부호 · 쉼(gap초) · 길이(maxlen자)에서 끊는다"""
    out, buf, t0, last_t = [], [], None, None
    for t, w in items:
        if buf and (t - last_t > gap or len(" ".join(buf)) + len(w) > maxlen):
            out.append((t0, " ".join(buf)))
            buf, t0 = [], None
        if t0 is None:
            t0 = t
        buf.append(w)
        last_t = t
        if re.search(r"[.?!。…]$", w):
            out.append((t0, " ".join(buf)))
            buf, t0 = [], None
    if buf:
        out.append((t0, " ".join(buf)))
    return out


def whisper_sentences(src, a, dur, lang):
    from faster_whisper import WhisperModel       # 무거워서 쓸 때만 (tools/words.py 와 같은 설정)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a}", "-t", f"{dur}", "-i", str(src), "-vn",
                          "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    m = WhisperModel("medium", device="cpu", compute_type="int8")
    segs, info = m.transcribe(x, language=lang)
    out = [(a + s.start, s.text.strip()) for s in segs if s.text.strip()]
    return out, getattr(info, "language", lang)


# ---------------------------------------------------------------- 줌/펀치인 · 화면 구성 · BGM (롱폼판 추가)
ZW, ZH = 480, 270               # 줌 추정용 회색 프레임 (10fps)


def zoom_scan(src, a, dur, fps_an=10):
    """연속 프레임 사이 배율을 ORB 특징점 매칭 + 유사변환(RANSAC)으로 추정. 반환 [(시각, log배율, 이동x, 이동y, 인라이어)]
    컷 직후 프레임(매칭 실패·인라이어 적음)은 None. «추정» — 화면 속 내용이 같이 움직이면(스크롤·그래픽) 틀릴 수 있다."""
    import cv2
    orb = cv2.ORB_create(nfeatures=600)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    out = []
    prev_kp = prev_des = None
    for i, fr in enumerate(pipe_frames(src, a, dur, fps_an, ZW, ZH, "gray")):
        kp, des = orb.detectAndCompute(fr, None)
        res = None
        if prev_des is not None and des is not None and len(kp) >= 12 and len(prev_kp) >= 12:
            m = bf.match(prev_des, des)
            if len(m) >= 12:
                p0 = np.float32([prev_kp[x.queryIdx].pt for x in m])
                p1 = np.float32([kp[x.trainIdx].pt for x in m])
                M, inl = cv2.estimateAffinePartial2D(p0, p1, method=cv2.RANSAC, ransacReprojThreshold=2.0)
                if M is not None and inl is not None and int(inl.sum()) >= 12:
                    sc = math.hypot(M[0, 0], M[1, 0])
                    if 0.7 < sc < 1.4:
                        res = (math.log(sc), float(M[0, 2]), float(M[1, 2]), int(inl.sum()))
        out.append((a + i / fps_an, res))
        prev_kp, prev_des = kp, des
    return out


def find_zooms(zs, cut_times, fps_an=10, min_total=0.04, min_step=0.004):
    """zs 의 log배율을 같은 방향으로 이어 붙여 줌 사건으로 묶는다. 배율 = exp(합). 컷 직후 한 칸은 무시.
    종류: 펀치(<=0.6초) · 빠른(<=2초) · 느린(그 이상)"""
    cut_set = {round(t, 1) for t in cut_times}
    ev, cur = [], None
    dt = 1.0 / fps_an
    for t, r in zs:
        near_cut = any(abs(t - c) < dt * 1.5 for c in cut_times)
        v = None if (r is None or near_cut) else r[0]
        if v is not None and abs(v) >= min_step:
            sign = 1 if v > 0 else -1
            if cur and cur["sign"] == sign and t - cur["last"] <= dt * 2.5:
                cur["sum"] += v
                cur["last"] = t
                cur["peak"] = max(cur["peak"], abs(v))
                cur["n"] += 1
            else:
                if cur:
                    ev.append(cur)
                cur = {"sign": sign, "t0": t - dt, "last": t, "sum": v, "peak": abs(v), "n": 1}
        else:
            if cur and t - cur["last"] > dt * 2.5:
                ev.append(cur)
                cur = None
    if cur:
        ev.append(cur)
    out = []
    for e in ev:
        if abs(e["sum"]) < min_total:
            continue
        d = e["last"] - e["t0"]
        kind = "펀치" if d <= 0.6 else ("빠른" if d <= 2.0 else "느린")
        out.append({"t0": e["t0"], "t1": e["last"], "scale": math.exp(e["sum"]), "dir": "in" if e["sign"] > 0 else "out",
                    "dur": d, "kind": kind, "peak_per_step": math.exp(e["peak"])})
    return out


def composition_scan(src, a, dur):
    """1초마다 한 프레임 -> 얼굴(LBP 캐스케이드) 가장 큰 것의 면적 비율로 거친 분류. «추정» — 눈으로 고쳐 쓴다.
    FACE_BIG(>=2.5%) 사람 큼 / FACE_SMALL(0.25~2.5%) 사람 작음(자료와 함께일 가능성) / 얼굴 없음(자료·그래픽·녹화)"""
    from skimage import data as skdata
    from skimage.feature import Cascade        # OpenCV 5 에는 CascadeClassifier 가 없어 scikit-image LBP 얼굴 검출기를 쓴다
    cas = Cascade(skdata.lbp_frontal_face_cascade_filename())
    rows = []
    for i, fr in enumerate(pipe_frames(src, a, dur, 1, 480, 270, "gray")):
        faces = cas.detect_multi_scale(img=fr, scale_factor=1.25, step_ratio=1.5, min_size=(24, 24), max_size=(270, 270))
        fa = 0.0
        if len(faces):
            fa = max(f["width"] * f["height"] for f in faces) / (480 * 270)
        edge = float((np.abs(np.diff(fr.astype(np.int16), axis=1)) > 40).mean())     # 글자·도형 많으면 큼
        cls = "사람큼" if fa >= 0.025 else ("사람작음" if fa >= 0.0025 else "얼굴없음")
        rows.append((a + i, fa, edge, cls))
    return rows



def bgm_estimate(src, a, dur):
    """BGM «추정» (말소리 섞인 원음에서): 50ms RMS(dBFS)의 하위 5% · 중앙값 · «-50dB 미만 비율».
    말 사이 쉼에서도 바닥이 -45dB 위에 있으면 깔린 소리(BGM·룸톤)가 있다. 쉼이 깊은 영상(-50dB 미만 10%+)은 BGM 없음.
    정확한 건 --stems(말소리 분리 후 측정). 반환 (p5, 중앙값, -50dB미만비율, 판정)"""
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{a}", "-t", f"{dur}", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000",
           "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    y = np.frombuffer(raw[:len(raw) // 4 * 4], np.float32)
    k = 800
    n = len(y) // k
    if n < 20:
        return None, None, None, "판단 불가"
    db = 20 * np.log10(np.sqrt((y[:n * k].reshape(n, k) ** 2).mean(1)) + 1e-9)
    p5, med = float(np.percentile(db, 5)), float(np.median(db))
    low = float(np.mean(db < -50))
    if low >= 0.10:
        v = "없음(추정: 쉼이 깊다)"
    elif p5 >= -45 and low < 0.03:
        v = "있음(추정: 바닥이 깔림)"
    else:
        v = "약함/애매(추정)"
    return p5, med, low, v


# ---------------------------------------------------------------- 말소리 분리 -> 효과음·BGM (롱폼판 추가, --stems)
SEP_CHUNK_S = 60


def stem_analysis(src, a, dur, out_dir):
    """torchaudio HDemucs(MUSDB+) 로 말소리(vocals)를 떼고 나머지(drums+bass+other = BGM+효과음)에서 측정.
    - BGM: 나머지 소리의 1초 RMS 중앙값(dBFS)과 «말소리 대비 dB». 바닥(하위10%)이 -60dB 위면 계속 깔림.
    - 효과음 후보(sfx): 나머지 소리가 직전 200ms 중앙값보다 SFX_JUMP_DB 이상 갑자기 커진 시각, 절대 크기 SFX_MIN_DB 이상.
      음악의 박자(드럼)도 걸릴 수 있으므로 «후보»·«추정». 처음 사용 시 모델 약 320MB 를 torch 캐시로 받는다.
    반환 dict. audio_stems.csv 에 후보 목록을 쓴다."""
    import torch
    from torchaudio.pipelines import HDEMUCS_HIGH_MUSDB_PLUS as B
    from scipy.signal import resample_poly
    SFX_JUMP_DB, SFX_MIN_DB = 9.0, -38.0
    model = B.get_model()
    model.eval()
    sr = B.sample_rate
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{a}", "-t", f"{dur}", "-i", str(src), "-vn", "-ac", "2", "-ar", str(sr),
           "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    y = np.frombuffer(raw[:len(raw) // 8 * 8], np.float32).reshape(-1, 2).T.copy()
    n_total = y.shape[1]
    voc_rms, acc_rms, acc_mono = [], [], []
    ch = SEP_CHUNK_S * sr
    for s0 in range(0, n_total, ch):
        seg = torch.from_numpy(y[:, s0:s0 + ch])[None]
        with torch.no_grad():
            o = model(seg)[0].numpy()                                  # [drums, bass, other, vocals]
        acc = o[0] + o[1] + o[2]
        voc = o[3]
        acc_mono.append(acc.mean(0))
        k = sr
        for arr, lst in ((voc.mean(0), voc_rms), (acc.mean(0), acc_rms)):
            m = len(arr) // k
            if m:
                lst += list(np.sqrt((arr[:m * k].reshape(m, k) ** 2).mean(1)) + 1e-9)
    acc_all = np.concatenate(acc_mono)
    voc_db = 20 * np.log10(np.array(voc_rms))
    acc_db = 20 * np.log10(np.array(acc_rms))
    # 효과음 후보: 10ms RMS 포락선
    hop = sr // 100
    m = len(acc_all) // hop
    env = 20 * np.log10(np.sqrt((acc_all[:m * hop].reshape(m, hop) ** 2).mean(1)) + 1e-9)
    cands, last = [], -1
    chunk_edges = {int(round(i * SEP_CHUNK_S * 100)) for i in range(1, int(dur // SEP_CHUNK_S) + 2)}
    for i in range(21, m - 12):
        prev = float(np.median(env[i - 20:i - 2]))
        peak = float(env[i:i + 6].max())
        if peak - prev >= SFX_JUMP_DB and peak >= SFX_MIN_DB and env[i] >= env[i - 1] and i - last >= 15:
            if any(abs(i - e) <= 30 for e in chunk_edges):              # 60초 조각 이음매 근처는 인공물 가능
                continue
            last = i
            seg22 = resample_poly(acc_all[max(0, i * hop - 441):i * hop + 9000], 1, 2).astype(np.float32)
            cands.append({"t": a + i / 100.0, "peak_db": peak, "jump_db": peak - prev, "kind": classify(seg22, 441 // 2 + 0, peak)})
    with open(out_dir / "audio_stems.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["time_s", "peak_db", "jump_db", "kind_estimated"])
        for c in cands:
            w.writerow([f"{c['t']:.2f}", f"{c['peak_db']:.1f}", f"{c['jump_db']:.1f}", c["kind"]])
    mins = dur / 60
    res = {"bgm_med_db": float(np.median(acc_db)), "bgm_p10_db": float(np.percentile(acc_db, 10)),
           "voc_med_db": float(np.median(voc_db)), "sfx_n": len(cands), "sfx_per_min": len(cands) / mins,
           "sfx_strict_per_min": sum(1 for c in cands if c["jump_db"] >= 20 and c["peak_db"] >= -30) / mins,
           "kinds": {}}
    for c in cands:
        res["kinds"][c["kind"]] = res["kinds"].get(c["kind"], 0) + 1
    res["verdict"] = ("BGM 뚜렷(추정)" if res["bgm_p10_db"] > -45 else ("BGM 약함(추정)" if res["bgm_med_db"] > -50 else "BGM 거의 없음(추정)"))
    return res


# ---------------------------------------------------------------- 시트 · 키프레임
class SheetJob:
    def __init__(self, name, cells, cols, cw=None):
        self.name, self.cells, self.cols = name, cells, cols      # cells = [0.25초 격자 번호]
        self.cw = cw                                              # None 이면 make_sheets 의 기본 칸 너비
        self.rows = math.ceil(len(cells) / cols)
        self.left = len(cells)
        self.canvas = None


def draw_cell(fr, label, is_cut, cw, ch):
    im = Image.fromarray(fr)
    d = ImageDraw.Draw(im)
    f = get_font(max(14, cw // 13))
    tw = d.textlength(label, font=f)
    d.rectangle([0, 0, tw + 10, f.size + 6], fill="black")
    d.text((5, 1), label, font=f, fill="yellow")
    if is_cut:
        d.rectangle([0, 0, cw - 1, ch - 1], outline="red", width=4)
    return im


def make_sheets(src, a, dur, jobs, cut_idx, cw, ch, out_dir):
    """모든 시트가 필요한 칸(0.25초 격자)을 한 번의 스트리밍으로 채운다"""
    need = {}
    for j in jobs:
        for slot, idx in enumerate(j.cells):
            need.setdefault(idx, []).append((j, slot))
    last = max(need) if need else -1
    for k, fr in enumerate(pipe_frames(src, a, dur, 4, cw, ch, "rgb24")):
        if k in need:
            label = fmt_t(a + k * 0.25)
            cell = draw_cell(fr, label, k in cut_idx, cw, ch)
            for j, slot in need.pop(k):
                jw = j.cw or cw
                jh = int(round(jw * ch / cw / 2)) * 2
                c2 = cell if jw == cw else draw_cell(fr, label, k in cut_idx, cw, ch).resize((jw, jh), Image.LANCZOS)
                if j.canvas is None:
                    j.canvas = Image.new("RGB", (j.cols * jw, j.rows * jh), "black")
                j.canvas.paste(c2, ((slot % j.cols) * jw, (slot // j.cols) * jh))
                j.left -= 1
                if j.left == 0:
                    j.canvas.save(out_dir / j.name, quality=85)
                    j.canvas = None
        if k >= last:
            break
    for j in jobs:                 # 영상이 먼저 끝난 시트는 있는 만큼 저장
        if j.canvas is not None:
            j.canvas.save(out_dir / j.name, quality=85)


def grab_keyframes(src, times, out_dir):
    done = []
    for n, t in enumerate(times):
        f = out_dir / f"kf_{n:03d}_{t:08.2f}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t}", "-i", str(src), "-frames:v", "1",
                        "-q:v", "2", str(f)], capture_output=True)
        if f.exists():
            done.append(f.name)
    return done


# ---------------------------------------------------------------- 본체
def main():
    ap = argparse.ArgumentParser(description="레퍼런스 영상 정독 해부")
    ap.add_argument("folder", help="폴더 경로 또는 영상ID (영상ID 면 _tmp/ref/<영상ID>)")
    ap.add_argument("--long", action="store_true", help="강의용 긴 영상 모드")
    ap.add_argument("--no-fine", dest="no_fine", action="store_true", help="0.5초 정밀 시트(fine_*) 생략")
    ap.add_argument("--cutsheets", action="store_true", help="컷마다 한 장짜리 시트(cut_*) 도 만든다 (기본 생략)")
    ap.add_argument("--stems", action="store_true", help="말소리 분리(HDemucs, CPU 8분에 약 3분) 후 BGM·효과음 후보 측정 -> audio_stems.csv")
    ap.add_argument("--from", dest="t_from", type=float, default=0.0)
    ap.add_argument("--to", dest="t_to", type=float, default=None)
    args = ap.parse_args()

    folder = Path(args.folder)
    if not folder.exists() and (WORK / "ref" / args.folder).exists():
        folder = WORK / "ref" / args.folder
    src = folder / "src.mp4"
    if not src.exists():
        raise SystemExit(f"src.mp4 가 없다: {folder}")
    info = {}
    if (folder / "src.info.json").exists():
        try:
            info = json.loads((folder / "src.info.json").read_text(encoding="utf-8"))
        except Exception:
            pass
    pr = probe(src)
    a = max(0.0, args.t_from)
    b = min(pr["dur"], args.t_to) if args.t_to else pr["dur"]
    dur = b - a
    if dur <= 0:
        raise SystemExit("구간 길이가 0 이하")
    long_mode = args.long
    if not long_mode and dur >= 120:
        print(f"[알림] 구간 {dur:.0f}초 >= 120초 -> --long 모드로 자동 전환")
        long_mode = True
    out = folder / "study"
    (out / "keyframes").mkdir(parents=True, exist_ok=True)
    portrait = pr["h"] > pr["w"]
    t_run0 = __import__("time").time()
    print(f"[{src.name}] {pr['w']}x{pr['h']} {pr['fps']:.2f}fps {pr['dur']:.1f}s  구간 {a:.1f}~{b:.1f}  모드={'long' if long_mode else 'short'}")

    # 1) 영상: 움직임 · 컷
    fps_an = 10 if long_mode else 30
    print("1/6 움직임·컷 분석 ...")
    diff, hchg = analyze_video(src, a, dur, fps_an)
    cut_i = find_cuts(diff, hchg)
    cut_t = [a] + [a + i / fps_an for i in cut_i]
    ends = cut_t[1:] + [b]
    with open(out / "cuts.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["cut", "start_s", "end_s", "length_s"])
        for n, (s, e) in enumerate(zip(cut_t, ends)):
            w.writerow([n + 1, f"{s:.2f}", f"{e:.2f}", f"{e - s:.2f}"])
    step = max(1, int(round(fps_an * 0.1)))
    with open(out / "motion.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["time_s", "motion_mean", "motion_max"])
        for i in range(0, len(diff), step):
            c = diff[i:i + step]
            w.writerow([f"{a + i / fps_an:.2f}", f"{c.mean():.2f}", f"{c.max():.2f}"])
    thr = max(4.0, float(np.percentile(diff, 90))) if len(diff) else 4.0
    pk_t = [a + i / fps_an for i in find_peaks(diff, thr)]

    # 1-2) 줌/펀치인 (롱폼판 추가)
    print("1b/6 줌·펀치인 검출 (ORB) ...")
    zs = zoom_scan(src, a, dur, 10)
    zooms = find_zooms(zs, cut_t[1:], 10)
    with open(out / "zoom.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["start_s", "end_s", "dur_s", "scale_x", "dir", "kind", "max_step_scale"])
        for z in zooms:
            w.writerow([f"{z['t0']:.2f}", f"{z['t1']:.2f}", f"{z['dur']:.2f}", f"{z['scale']:.3f}", z["dir"], z["kind"], f"{z['peak_per_step']:.3f}"])
    print("1c/6 화면 구성 (얼굴 크기) ...")
    comp = composition_scan(src, a, dur)
    with open(out / "composition.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["time_s", "face_area", "edge_density", "class_estimated"])
        for t, fa, ed, c in comp:
            w.writerow([f"{t:.0f}", f"{fa:.4f}", f"{ed:.3f}", c])
    comp_cnt = {}
    for _t, _fa, _ed, c in comp:
        comp_cnt[c] = comp_cnt.get(c, 0) + 1
    # 얼굴 있음 -> 없음 으로 바뀐 횟수 = 사람 화면에서 자료/그래픽 화면으로 간 횟수의 거친 값
    g_in = sum(1 for i in range(1, len(comp)) if comp[i - 1][3] != "얼굴없음" and comp[i][3] == "얼굴없음")
    bg_p5, bg_med, bg_low, bg_verdict = bgm_estimate(src, a, dur) if pr["has_audio"] else (None, None, None, "소리 없음")
    stems = None
    if args.stems and pr["has_audio"]:
        print("1d/6 말소리 분리 -> BGM·효과음 후보 (--stems) ...")
        stems = stem_analysis(src, a, dur, out)

    # 2) 소리
    onsets, beats, bpms, lufs, tp, lra = [], [], [], None, None, None
    if pr["has_audio"]:
        print("2/6 소리 타격·박자 분석 ...")
        onsets, beats, bpms = analyze_audio(src, a, dur)
        lufs, tp, lra = loudness(src, a, dur)
    strong = [o for o in onsets if o["jump"] >= STRONG_JUMP_DB]
    bpm = float(np.median(bpms)) if bpms else None
    with open(out / "audio.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["time_s", "level_db", "jump_db", "strong", "kind_estimated"])
        for o in onsets:
            w.writerow([f"{o['t']:.3f}", f"{o['db']:.1f}", f"{o['jump']:.1f}", int(o["jump"] >= STRONG_JUMP_DB), o["kind"]])
        f.write(f"# bpm_median,{'' if bpm is None else f'{bpm:.1f}'}\n")
        f.write("# beats_s," + " ".join(f"{t:.2f}" for t in beats) + "\n")
        f.write(f"# LUFS_integrated,{lufs}\n# true_peak_dBFS,{tp}\n# LRA_LU,{lra}\n")
        f.write("# kind 는 소리 모양으로 짐작한 «추정» (짧은 고역=클릭/틱, 긴 상승=휙/라이저, 저역 큰=쿵)\n")

    # 3) sync.txt
    print("3/6 맞춤 계산 ...")

    def near_ratio(ts, ref):
        if not ts or not ref:
            return None
        r = np.array(ref)
        return float(np.mean([np.min(np.abs(r - t)) <= TOL_S for t in ts]))

    def pct(x):
        return "측정 불가" if x is None else f"{x * 100:.0f}%"

    st_t = [o["t"] for o in strong]
    ncuts = len(cut_t)
    hits_per_cut = len(strong) / ncuts if ncuts else 0
    sync = [
        f"맞춤 허용 = ±2프레임 = ±{TOL_S * 1000:.0f}ms (30fps 기준). 움직임 분석 해상도 {fps_an}fps"
        + (" — long 모드라 실제 해상도는 ±100ms, 참고용" if fps_an < 30 else ""),
        f"움직임 봉우리 {len(pk_t)}개 (문턱 {thr:.1f})",
        f"  봉우리가 소리 타격(강한 onset {len(st_t)}개)과 맞는 비율: {pct(near_ratio(pk_t, st_t))}",
        f"  봉우리가 박(beat {len(beats)}개)과 맞는 비율: {pct(near_ratio(pk_t, beats))}",
        f"컷 {ncuts}개 (첫 컷 = 구간 시작 포함)",
        f"  컷이 소리 타격과 맞는 비율: {pct(near_ratio(cut_t[1:], st_t))}",
        f"  컷이 박과 맞는 비율: {pct(near_ratio(cut_t[1:], beats))}",
        f"컷당 평균 소리 타격 수: {hits_per_cut:.2f}  (강한 onset 기준; 전체 onset {len(onsets)}개)",
        "※ 말소리 음절도 onset 으로 잡힌다. 말이 많은 영상은 타격 수가 부풀려지니 audio.csv 의 kind 를 같이 볼 것.",
    ]
    (out / "sync.txt").write_text("\n".join(sync) + "\n", encoding="utf-8", newline="\n")

    # 4) 말
    print("4/6 말(자막/whisper) ...")
    _il = (info.get("language") or "ko")[:2].lower()
    subs = find_subs(folder, info, _il if _il in ("ko", "en") else "ko")
    sents = []
    if subs:
        path, kind = subs
        items = parse_json3(path) if path.suffix == ".json3" else parse_vtt(path)
        sents = to_sentences(items)
        src_desc = f"{kind} 자막 ({path.name})"
    elif pr["has_audio"]:
        lang = "ko" if (info.get("language") or "ko").startswith("ko") else None
        sents, dl = whisper_sentences(src, a, dur, lang)
        src_desc = f"faster-whisper medium int8 CPU (언어 {dl})"
    else:
        src_desc = "소리 없음"
    sents = [(t, s) for t, s in sents if a - 0.01 <= t <= b]
    lines = ["# 대본 (시각 붙은 말)", "", f"- 출처: {src_desc}", f"- 구간: {fmt_t(a)} ~ {fmt_t(b)}", ""]
    lines += [f"[{fmt_t(t)}] {s}" for t, s in sents]
    (out / "transcript.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    # 5) 접촉 시트
    print("5/6 접촉 시트 ...")
    cut_idx = {int(round((t - a) / 0.25)) for t in cut_t[1:]}
    total = int(dur / 0.25) + 1
    for old in list(out.glob("sheet_*.jpg")) + list(out.glob("cut_*.jpg")) + list(out.glob("fine_*.jpg")):
        old.unlink()
    jobs = []
    if not long_mode:
        cw = 300 if portrait else 360
        per = 16
        for n, s in enumerate(range(0, total, per)):
            cells = list(range(s, min(total, s + per)))
            jobs.append(SheetJob(f"sheet_{n:03d}_{a + cells[0] * 0.25:.2f}-{a + cells[-1] * 0.25:.2f}.jpg", cells, 4))
    else:
        cw = 480
        per = 12
        grid = list(range(0, total, 40))                # 10초 = 0.25초 x 40
        for n, s in enumerate(range(0, len(grid), per)):
            cells = grid[s:s + per]
            jobs.append(SheetJob(f"sheet_{n:03d}_{a + cells[0] * 0.25:.2f}-{a + cells[-1] * 0.25:.2f}.jpg", cells, 4))
        if not args.no_fine:                            # 0.5초 간격 5x4 = 10초 한 장 (롱폼판 추가)
            fgrid = list(range(0, total, 2))
            for n, s0 in enumerate(range(0, len(fgrid), 20)):
                cells = fgrid[s0:s0 + 20]
                jobs.append(SheetJob(f"fine_{n:03d}_{a + cells[0] * 0.25:.2f}-{a + cells[-1] * 0.25:.2f}.jpg", cells, 5, 384))
        for n, (s, e) in enumerate(zip(cut_t, ends)):
            if n >= 300 or not args.cutsheets:
                break
            i0 = int(round((s - a) / 0.25))
            i1 = max(i0, min(total - 1, int((e - a) / 0.25 - 1e-6)))
            span = i1 - i0 + 1
            m = min(12, span)
            ks = sorted({i0 + int(round(q * (span - 1) / max(1, m - 1))) for q in range(m)})
            jobs.append(SheetJob(f"cut_{n:03d}_{s:.2f}-{e:.2f}.jpg", ks, 4))
    ch = int(round(cw * pr["h"] / pr["w"] / 2)) * 2
    make_sheets(src, a, dur, jobs, cut_idx, cw, ch, out)

    # 6) 키프레임
    print("6/6 키프레임 ...")
    kt = [t + 1.0 / fps_an for t in cut_t]
    kt[0] = cut_t[0]
    if len(kt) > KEYFRAME_MAX:
        kt = kt[::math.ceil(len(kt) / KEYFRAME_MAX)]
    for old in (out / "keyframes").glob("kf_*.jpg"):
        old.unlink()
    kfs = grab_keyframes(src, [min(t, max(a, b - 0.05)) for t in kt], out / "keyframes")

    # summary
    sheets = sorted(p.name for p in out.glob("sheet_*.jpg")) + sorted(p.name for p in out.glob("fine_*.jpg"))
    cutsheets = sorted(p.name for p in out.glob("cut_*.jpg"))
    lens = [e - s for s, e in zip(cut_t, ends)]
    mins = dur / 60
    S = [
        f"# 해부 요약 — {info.get('title', src.name)}", "",
        f"- 원본: {src} ({pr['vcodec']}, {pr['w']}x{pr['h']}, {pr['fps']:.2f}fps, 전체 {pr['dur']:.1f}초)",
        f"- 본 구간: {a:.1f} ~ {b:.1f}초 ({dur:.1f}초) · 모드 {'long' if long_mode else 'short'} · 움직임 분석 {fps_an}fps",
        f"- 컷 수: {ncuts} · 평균 컷 길이 {np.mean(lens):.2f}초 (최단 {min(lens):.2f} / 최장 {max(lens):.2f})",
        f"- 소리 타격: 강한 것 {len(strong)}개 ({len(strong) / mins:.1f}/분) · 전체 onset {len(onsets)}개 ({len(onsets) / mins:.1f}/분) · 컷당 {hits_per_cut:.2f}",
        (f"- LUFS {lufs} · 트루피크 {tp} dBFS · LRA {lra} LU" if pr["has_audio"] else "- 소리 없음"),
        f"- BPM(추정, 중앙값) {'-' if bpm is None else f'{bpm:.1f}'} · 박 {len(beats)}개",
        f"- 줌/펀치인 후보(추정) {len(zooms)}건 ({len(zooms) / mins:.1f}/분): "
        + ", ".join(f"{k} {sum(1 for z in zooms if z['kind'] == k)}" for k in ("펀치", "빠른", "느린")) + " — zoom.csv",
        f"- 화면 구성(1초 표본, 얼굴 크기 기준 거친 추정): " + " · ".join(f"{k} {v / max(1, len(comp)) * 100:.0f}%" for k, v in comp_cnt.items())
        + f" · 얼굴→얼굴없음 전환 {g_in}회 ({g_in / mins:.1f}/분, 자료/그래픽 화면 진입의 거친 값)",
        f"- BGM(원음 추정): {bg_verdict}" + ("" if bg_p5 is None else f" (50ms RMS 하위5% {bg_p5:.0f}dB · 중앙값 {bg_med:.0f}dB · -50dB 미만 {bg_low * 100:.0f}%)"),
        ("" if stems is None else f"- 말소리 분리 측정(추정): {stems['verdict']} · 말소리 외 소리 중앙값 {stems['bgm_med_db']:.0f}dB / 하위10% {stems['bgm_p10_db']:.0f}dB (말소리 중앙값 {stems['voc_med_db']:.0f}dB) · 효과음 후보 {stems['sfx_n']}개 ({stems['sfx_per_min']:.1f}/분, 엄격 ≥20dB·≥-30dBFS {stems['sfx_strict_per_min']:.1f}/분 — BGM 곡이 있으면 느슨한 값은 과대) {stems['kinds']} — audio_stems.csv"),
        f"- 컷/분 {ncuts / mins:.1f}",
        f"- 말: {src_desc} · {len(sents)}문장",
        "- 맞춤: " + " / ".join(l.strip() for l in sync[2:4] + sync[5:7]),
        "", "## 시트 (눈으로 볼 것)",
    ]
    S += [f"- {n}" for n in sheets]
    if cutsheets:
        S += ["", "### 컷별 시트"] + [f"- {n}" for n in cutsheets]
    S += ["", f"## 키프레임 {len(kfs)}장 (keyframes/)", "",
          "## 파일", "- transcript.md · cuts.csv · motion.csv · zoom.csv · composition.csv · audio.csv · sync.txt · summary.md"]
    (out / "summary.md").write_text("\n".join(S) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(S))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""파트너센터 자동 — 연출표 → plan.json(compose) + cues.json(sfx_bus).

장면 시각은 자막 줄(captions_v1.json)에서 글로 찾고(cap), 단어 시각이 필요하면 강제 정렬(word).
강조 위치는 OCR(ocr.json, 녹화 원본 시각)에서 글자로 찾고(ocr_box), 못 찾으면 화면을 보고 잰 기본값.
연출 근거: situation-playbook PB-02(실화면 확대 + 값 강조, 외부 호평 1위) · PB-05(개념 장면) · fusion-1013 2~4장.
"""
import json
import sys
from types import SimpleNamespace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
TMP = ROOT / "_tmp" / "pc"
CAPS = json.load(open(TMP / "captions_v1.json", encoding="utf-8"))["captions"]
EDIT = json.load(open(TMP / "edit.json", encoding="utf-8"))["items"]
V1 = sorted((i for i in EDIT if i["track"] == "V1"), key=lambda i: i["t0"])
OCR = json.load(open(TMP / "ocr.json", encoding="utf-8")) if (TMP / "ocr.json").exists() else None
LOGO = ROOT / "소재" / "pc" / "logo_tile"
CARD = ROOT / "소재" / "pc" / "cards"
_al = None
_wcache = {}
LOG = []


def cap(text, after=0.0):
    for c in CAPS:
        if c["t0"] >= after - 1e-6 and text in c["text"]:
            return SimpleNamespace(**c)
    raise KeyError(text)


def word(text, w, after=0.0):
    """자막 줄 안 낱말 w 의 말 시작(강제 정렬)."""
    global _al
    c = vars(cap(text, after))
    key = (c["t0"], w)
    if key in _wcache:
        return _wcache[key]
    import soundfile as sf
    from tools.auto.ko_align import Aligner
    if _al is None:
        _al = (Aligner(), sf.read(str(TMP / "a16k.wav"), dtype="float32"))
    al, (x, sr) = _al
    a = c["t0"] - 0.3
    ws = c["text"].split()
    res = al.align(x[int(a * sr):int((c["t1"] + 0.3) * sr)], ws)
    k = next(i for i, s in enumerate(ws) if w in s)
    t = a + res[k][0] if res[k] else c["t0"]
    _wcache[key] = round(t, 3)
    return _wcache[key]


def src_time(t):
    for it in V1:
        if it["t0"] <= t < it["t1"]:
            return it["s0"] + (t - it["t0"]), it["name"]
    return None, None


def ocr_box(text, t, near=None, fallback=None, pad=6):
    """시퀀스 시각 t 의 녹화 화면에서 text 가 들어 있는 OCR 칸. near=(x,y) 면 그 근처 것."""
    if OCR:
        s, name = src_time(t)
        if s is not None and "화면" in (name or ""):
            smp = min(OCR["samples"], key=lambda m: abs(m["s"] - s))
            if abs(smp["s"] - s) < 1.0:
                hits = [b for b in smp["boxes"] if text in b[4].replace(" ", "")]
                if hits:
                    if near:
                        hits.sort(key=lambda b: ((b[0] + b[2]) / 2 - near[0]) ** 2 + ((b[1] + b[3]) / 2 - near[1]) ** 2)
                    b = hits[0]
                    if near and ((b[0] + b[2]) / 2 - near[0]) ** 2 + ((b[1] + b[3]) / 2 - near[1]) ** 2 > 250 ** 2:
                        LOG.append(f"{t:.1f} «{text}» OCR 칸이 기본값에서 멀다 → 기본값")
                    else:
                        LOG.append(f"{t:.1f} «{text}» OCR {[int(v) for v in b[:4]]}")
                        return [b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad]
    LOG.append(f"{t:.1f} «{text}» 기본값 {fallback}")
    return fallback


cams, fx, cues = [], [], []


def zoom(t0, t1, box, q=(1080, 470), zmax=1.7, fill=0.62):
    cams.append(dict(t0=round(t0, 3), t1=round(t1, 3), box=box, q=list(q), zmax=zmax, fill=fill, tin=0.45, tout=0.45))
    cues.append(dict(t=round(t0 + 0.22, 3), role="zoom_in"))
    cues.append(dict(t=round(t1 - 0.22, 3), role="zoom_out"))


def brush(t0, t1, box, color=(255, 70, 70), draw=0.35, kind="brush_rect", snd=True):
    pts = [[box[0], box[1]], [box[2], box[3]]] if kind == "brush_rect" else [[box[0], box[3] + 4], [box[2], box[3] + 4]]
    fx.append(dict(kind=kind, t0=round(t0, 3), t1=round(t1, 3), pts=pts, color=list(color), width=7, draw=draw))
    if snd:
        n = sum(1 for c in cues if c["role"].startswith("brush"))
        cues.append(dict(t=round(t0, 3), role=("brush", "brush2")[n % 2], dur=draw + 0.05))


def image(t0, t1, src, xy, w=None, layer="under", move=None, snd=None, s0=0.92):
    f = dict(kind="image", t0=round(t0, 3), t1=round(t1, 3), src=str(src), xy=list(xy), layer=layer, s0=s0)
    if w:
        f["w"] = w
    if move:
        f["move"] = move
    fx.append(f)
    if snd:
        cues.append(dict(t=round(t0 + 0.02, 3), role=snd))


def chip(t0, t1, text, xy, snd="chip"):
    fx.append(dict(kind="chip", t0=round(t0, 3), t1=round(t1, 3), text=text, xy=list(xy), size=38, layer="under"))
    cues.append(dict(t=round(t0 + 0.02, 3), role=snd))


# ───────── 장면 ─────────
# S2 매체 로고 → 유입 경로 자동 구분 (PB-05 개념 + 실화면 강조) 46.9~73.7
t_meta = word("메타에서도", "메타"); t_g = word("구글 애즈", "구글"); t_dg = word("당근에서도", "당근")
t_sort = cap("자동으로 유입 경로를").t0
Y = 110                                               # 표 위 빈 흰 곳(도구 줄 오른쪽) — 화면 글자와 겹치지 않게
logos1 = [(t_meta, "Meta_Platforms_Inc._logo.png", 1150), (t_g, "Google_Ads_logo.png", 1490), (t_dg, "DaangnMarket_logo.png", 1640)]
for k, (t, f, x) in enumerate(logos1):
    image(t, t_sort + 1.4, LOGO / f, (x, Y), move=[[t_sort + 0.2 + 0.08 * k, t_sort + 1.2], [1030 - (90 if "Meta" in f else 0), 520, 0.35]],
          snd=("pop", "chip", "chip2")[k])
cues.append(dict(t=round(t_sort + 0.75, 3), role="swoosh"))
col = ocr_box("유입경로", cap("인스타그램에서 들어왔지만").t0, near=(1120, 460), fallback=[1060, 440, 1180, 480])
brush(cap("인스타그램에서 들어왔지만").t0, cap("구분 값을 다 지정해서").t1, [col[0] - 20, col[1] - 6, col[2] + 170, 1000])
t_k, t_tt, t_nv = word("카카오면 카카오", "카카오면"), word("틱톡이면 틱톡", "틱톡이면"), word("네이버면 네이버", "네이버면")
endk = cap("이렇게 해주기 때문에").t0
for k, (t, f, x) in enumerate([(t_k, "KakaoTalk_logo.png", 1120), (t_tt, "Tiktok_logo.png", 1310), (t_nv, "Naver_Logotype.png", 1500)]):
    image(t, endk + 0.4, LOGO / f, (x, Y), snd=("pop", "chip", "chip2")[k])

# S3 알림톡 두 갈래 — 텔레그램(직원 방) · 카카오 알림톡(고객). 실제 화면은 고객 정보라 모자이크 + 체험병원 예시로 다시 그린 카드
t_tg = cap("텔레그램에서 먼저").t0; t_kk = cap("고객님께도 내 카카오").t0; MOS = json.load(open(TMP / "mosaic_boxes.json", encoding="utf-8"))
TGW = [m for m in MOS if m["box"][2] == 1920]
t_end3 = TGW[0]["t1"]                                # 텔레그램 창이 끝날 때까지(창 전체 모자이크 위)
fx.append(dict(kind="dim", t0=round(t_tg - 0.1, 3), t1=round(t_end3, 3)))
image(t_tg, t_end3, CARD / "tg.png", (420, 120), w=780, snd="chat")
image(t_kk, t_end3, CARD / "kk.png", (1225, 320), w=680, snd="bell")

# S4 진행 상태 → 1차 부재 → 알림톡 같이 발송 (실화면 확대 + 값 강조)
t4 = cap("자, 신규 부분 클릭을").t0
zoom(t4 + 0.3, cap("DB가 넘어가면서").t0, [720, 450, 1200, 910])
# (10-13 넣을 때 검수) 1차 부재·«네» 강조는 뺌 — 말이 클릭보다 늦어 획이 떴을 땐 화면이 이미 바뀌어 엉뚱한 칸을 가리켰다. 확대만 남긴다.

# S5 Shift + 휠 (조작 키 칩)
chip(cap("그럴 때는 Shift를").t0, cap("알고 계시면 될 것 같고", after=222).t0, "Shift + 휠  →  좌우 이동", (1240, 160))
chip(cap("Shift를 떼고").t0, cap("알고 계시면 될 것 같고", after=222).t0, "휠  →  위아래", (1240, 240), snd="chip2")

# S6 담당자 지정 — 중복 통화 방지
t6 = cap("사람 클릭을 하면").t0
zoom(t6, cap("그래서 사람이 걸려 있는").t1, [1560, 430, 1910, 720], q=(1100, 470))
b = ocr_box("한체험", cap("라고 하면 사람을 한체험").t0 + 1.0, near=(1745, 552), fallback=[1690, 532, 1805, 572])
brush(word("라고 하면 사람을 한체험", "한체험"), cap("그래서 사람이 걸려 있는").t1, b)

# S7 상태 라벨 직접 만들기
zoom(cap("라벨 수정 버튼을").t0, cap("적용하기 버튼을").t1, [1370, 450, 1810, 1000], q=(1080, 470))

# S8 DB 감도 별점
b = ocr_box("★", cap("최하윤 님 통화했는데").t0 + 1.0, near=(1745, 555), fallback=[1680, 540, 1810, 572])
brush(word("그러면 별 5개", "별"), cap("평가가 아니라 여기는").t0, b, kind="underline", color=(255, 205, 40))

# S10 예약 확정 → 전날 자동 알림톡 (개념 카드 — 화면의 실제 값 10월 7일 09:00 · 최하윤)
t10 = cap("이 시간과 이름과").t0; t10e = cap("여기에만 옮겨져").t1
fx.append(dict(kind="dim", t0=round(t10 - 0.1, 3), t1=round(t10e, 3)))
image(t10, t10e, CARD / "cal.png", (560, 175), w=732, snd="clear")
image(cap("전날이 됐네").t0, t10e, CARD / "kk2.png", (1170, 505), w=660, snd="bell")

# S11 업데이트 댓글 — 입력 칸
b = ocr_box("답", cap("1차 통화 시").t0 + 0.5, near=(1490, 300), fallback=[1095, 235, 1895, 395])
brush(cap("1차 통화 시").t0, cap("아, 지금 이런 내용이").t1, [1095, 235, 1895, 395])

# S12 부재 터치
b = ocr_box("터치완료", cap("그러면 터치 완료").t0 + 1.0, near=(1580, 552), fallback=[1505, 535, 1660, 570])
brush(cap("그러면 터치 완료").t0, cap("받을 때까지 계속").t1, b)

# S13 태그 · 내 알림
zoom(cap("하면 직원분들 이렇게").t0 - 0.2, cap("태그가 됐다고").t1, [1090, 230, 1880, 720], q=(1000, 470))
zoom(cap("내 알림 칸에 들어오면").t0, cap("그쪽 탭으로 자동으로").t1, [1260, 180, 1840, 900], q=(1000, 480))

# S14 구매 완료 → 매출 자동 등록
b = ocr_box("100,000", cap("권유나 님 보톡스 10만").t0 + 0.5, near=(1265, 555), fallback=[1170, 538, 1360, 575])
brush(word("권유나 님 보톡스 10만", "10만"), cap("이렇게 자동으로 등록을").t1, b)
b = ocr_box("3,360,000", cap("지금 매출 나온 거").t0 + 0.5, near=(1265, 812), fallback=[1180, 795, 1360, 830])
brush(cap("지금 매출 나온 거").t0, cap("이렇게 자동으로 등록을").t1, b, kind="underline", color=(255, 205, 40))

# S14b 텔레그램 구매 완료 대화(실제 방은 고객 정보 → 창 전체 모자이크 + 예시 카드). 화면이 오갈 때마다 같이
for k, m in enumerate(TGW[1:]):
    fx.append(dict(kind="dim", t0=m["t0"], t1=m["t1"]))
    image(m["t0"], m["t1"], CARD / "buy.png", (560, 110), w=780, snd=("chat", None, None)[min(k, 2)], s0=0.96)

# S15 담당자 카드(사장님 예외: 담당자 이름·대표 번호는 가리지 않음)
brush(word("여기 여성분 얼굴", "얼굴"), cap("사람마다 담당자가").t1, [1795, 940, 1910, 1050])
zoom(cap("눌러보시면 ○○○").t0 + 0.6, cap("저한테 연락 바로 주세요").t1, [1490, 290, 1895, 900], q=(1050, 520))

# S16 광고 애널리틱스 — 가이드(위험 수치) · 지표
zoom(cap("눌러보시면 위험 수치").t0, cap("그냥 그렇게 이해하시면").t1, [395, 540, 860, 780], q=(1060, 470))
brush(cap("여기서 DB수, 단가").t0, cap("다 나오고요", after=1006).t1, [300, 215, 1895, 485])

# S17 알림톡 도착·실패
brush(cap("이렇게 실시간으로 지금 잘 도착").t0, cap("도착했다").t1, [315, 325, 1385, 400])

# S18 랜딩 섹션별 이탈
zoom(cap("지금 섹션 0, 1, 2").t0, cap("확인이 가능하시겠죠?", after=1229).t1, [925, 455, 1875, 735], q=(1000, 470))

# S20 열람 권한 — 고른 사람
zoom(cap("열람 권한 해가지고").t0, cap("이렇게 잠금 표시가").t1, [700, 440, 1220, 700], q=(980, 470))
b = ocr_box("고른사람", cap("또는 고른 사람에서").t0 + 0.3, near=(1120, 555), fallback=[1050, 530, 1195, 585])
brush(word("또는 고른 사람에서", "고른"), cap("여기서 팀장님이나").t1, b)

plan = {
    "edit": str(TMP / "edit.json"), "media_dirs": ["D:/26년 10월/261012"],
    "audio": "D:/26년 10월/261006/자동화 MP4/파트너센터 자동.mp4",
    "sfx_wav": str(TMP / "sfx_bus.wav"),
    "captions": str(TMP / "captions_v1.json"),
    "caption_style": {"font": "C:/Users/user/AppData/Local/Microsoft/Windows/Fonts/GmarketSansMedium.otf", "size": 48, "stroke": 4,
                      "padx": 12, "pady": 35, "radius": 8, "cy": 1011, "alpha": 0.616},
    "chip_font": "C:/Users/user/AppData/Local/Microsoft/Windows/Fonts/GmarketSansBold.otf",
    "pip": {"cx": 154.76, "cy": 929.85, "r": 150.64},
    "mosaic": str(TMP / "mosaic_boxes.json"),
    "cams": sorted(cams, key=lambda c: c["t0"]), "fx": fx,
    "out": str(ROOT / "납품" / "파트너센터_자동" / "파트너센터_자동.mp4"),
}
json.dump(plan, open(TMP / "plan.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(sorted(cues, key=lambda c: c["t"]), open(TMP / "cues.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(TMP / "plan_log.txt", "w", encoding="utf-8").write("\n".join(LOG))
print(f"카메라 {len(cams)} · 연출 {len(fx)} · 효과음 큐 {len(cues)}")
# 카메라끼리 겹침 검사
cs = sorted(cams, key=lambda c: c["t0"])
for a, b2 in zip(cs, cs[1:]):
    if b2["t0"] < a["t1"]:
        print("★ 카메라 겹침", a["t0"], b2["t0"])

# ── 넣을 때 검수(규칙 3): 화면 고정 연출(이미지·칩)이 사람 PIP·자막 자리·서로와 겹치지 않는지
from PIL import Image as _I
PIP = (0, 776, 308, 1080); CAPZ = (330, 970, 1590, 1055)


def _rect(f):
    if f["kind"] == "image":
        im = _I.open(f["src"]); w = f.get("w", im.width); h = round(im.height * w / im.width)
        return (f["xy"][0], f["xy"][1], f["xy"][0] + w, f["xy"][1] + h)
    if f["kind"] == "chip":
        return (f["xy"][0], f["xy"][1], f["xy"][0] + 26 * len(f["text"]) + 80, f["xy"][1] + 70)


def _hit(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


bad = 0
fixed = [f for f in fx if f["kind"] in ("image", "chip")]
for f in fixed:
    r = _rect(f)
    for z, nm in ((PIP, "사람 PIP"), (CAPZ, "자막 자리")):
        if _hit(r, z):
            print(f"★ 겹침 {f['t0']:.1f} {Path(f.get('src', f.get('text', ''))).name} ↔ {nm} {r}"); bad += 1
    if r[2] > 1920 or r[3] > 1080 or r[0] < 0 or r[1] < 0:
        print(f"★ 화면 밖 {f['t0']:.1f} {r}"); bad += 1
for i, a in enumerate(fixed):
    for b in fixed[i + 1:]:
        if a["t0"] < b["t1"] and b["t0"] < a["t1"] and not a.get("move") and not b.get("move") and _hit(_rect(a), _rect(b)):
            print(f"★ 연출끼리 겹침 {a['t0']:.1f} ↔ {b['t0']:.1f}"); bad += 1
print("겹침 검사:", "없음" if not bad else f"{bad}건")

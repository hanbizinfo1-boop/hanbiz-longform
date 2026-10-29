# -*- coding: utf-8 -*-
r"""성제관 썸네일 틀 — 장면 그림 위에 고정 틀로 글자를 얹는다 (study/thumb-1015.md 규칙 v1).

    python .claude/skills/longform/scripts/thumb_compose.py <spec.json>

spec.json:
  {"out": "납품/성제관01_썸네일/썸네일_A.jpg",
   "scene": "_tmp/thumbs/gen/ep1_A.png", "crop_y": 40,          # 원본에서 16:9 로 자를 위쪽 시작(원본 px)
   "line1": "사장님 99%가 모르는", "line2": "AI 활용법 10가지", "line2_color": "yellow"|"red",
   "inner": {"text": "이걸 밤새 내가 했다니..", "x": 70, "y": 40, "size": 46},      # 속마음(선택, 출력 px)
   "screens": [{"box": [x0,y0,x1,y1], "lines": [["user","리뷰 10개 답글 써 줘"], ["ai","..."]]}],  # 원본 px — 화면 속 읽히는 글
   "tables": [{"box": [x0,y0,x1,y1], "title": "정산 내역", "rows": [["주문 금액","12,000원"], ["배달비","-3,300원","red"]], "total": ["정산 금액","5,400원"], "size": 30}],  # 원본 px — 정산서·표 화면(10-23)
   "marks": [{"box": [x0,y0,x1,y1]}],                           # 빨간 네모 표시(출력 px)
   "labels": [{"box": [x0,y0,x1,y1], "text": "이거 알려 줘"}],    # 그림 속 말풍선에 글만(원본 px)
   "arrow": {"x": 640, "y": 250}}                                # 빨간 화살표(선택, 출력 px)
틀(고정): 1280×720 · 아래 45% 두 줄(1줄 흰 · 2줄 노랑/빨강) · 왼쪽 정렬 · 배민 도현체 · 검정 테두리 + 그림자 · 아래로 어두워지는 받침(단색 판 아님).
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1280, 720
FONT_DIR = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts")
HEAD = os.path.join(FONT_DIR, "BMDOHYEON_otf.otf")
HAND = os.path.join(FONT_DIR, "Cafe24Danjunghae-v2.0.otf")
UI = "C:/Windows/Fonts/malgun.ttf"
COLORS = {"yellow": (255, 212, 0), "red": (255, 59, 48), "white": (255, 255, 255)}
MARGIN = 44


def fit_font(path, text, max_w, start):
    s = start
    while s > 40:
        f = ImageFont.truetype(path, s)
        if f.getbbox(text)[2] <= max_w:
            return f
        s -= 2
    return ImageFont.truetype(path, s)


def draw_screen(img, box, lines, size=None):
    # 원본 화면 영역에 읽히는 대화 글을 그린다(회색 줄 대체 — 절대금지 10-07)
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    d.rectangle(box, fill=(250, 251, 253))
    h = y1 - y0
    fs = size or max(12, int(h * 0.075))   # 좁은 세로 화면은 size 로 직접
    f = ImageFont.truetype(UI, fs)
    y = y0 + int(h * 0.08)
    for who, text in lines:
        tw = f.getbbox(text)[2]
        pad = int(fs * 0.6)
        if who == "user":
            bx1 = x1 - int((x1 - x0) * 0.06); bx0 = bx1 - tw - pad * 2
            fill = (225, 232, 245)
        else:
            bx0 = x0 + int((x1 - x0) * 0.06); bx1 = bx0 + tw + pad * 2
            fill = (240, 241, 244)
        bh = fs + pad * 2
        d.rounded_rectangle([bx0, y, bx1, y + bh], radius=int(fs * 0.6), fill=fill)
        d.text((bx0 + pad, y + pad - 2), text, font=f, fill=(30, 30, 30))
        y += bh + int(fs * 0.5)


def draw_table(img, box, title, rows, total=None, size=None):
    # 원본 화면 영역에 읽히는 표(항목 · 금액)를 그린다 — 정산서·영수증 화면(10-23 사장의 시스템 3편)
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    d.rectangle(box, fill=(250, 251, 253))
    w, h = x1 - x0, y1 - y0
    fs = size or max(12, int(h * 0.05))
    f = ImageFont.truetype(UI, fs)
    fb = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", int(fs * 1.15))
    px = int(w * 0.07)
    y = y0 + int(h * 0.05)
    if title:
        d.text((x0 + px, y), title, font=fb, fill=(25, 25, 25)); y += int(fs * 2.0)
        d.line([x0 + px, y - int(fs * 0.5), x1 - px, y - int(fs * 0.5)], fill=(200, 202, 208), width=2)
    for r in rows:
        col = COLORS.get(r[2], (30, 30, 30)) if len(r) > 2 else (30, 30, 30)
        d.text((x0 + px, y), r[0], font=f, fill=(70, 70, 75))
        d.text((x1 - px - f.getbbox(r[1])[2], y), r[1], font=f, fill=col)
        y += int(fs * 1.75)
    if total:
        y += int(fs * 0.3)
        d.line([x0 + px, y, x1 - px, y], fill=(40, 40, 45), width=3); y += int(fs * 0.6)
        d.text((x0 + px, y), total[0], font=fb, fill=(25, 25, 25))
        d.text((x1 - px - fb.getbbox(total[1])[2], y), total[1], font=fb, fill=COLORS["red"])


def outlined(d, xy, text, font, fill, stroke=8, accent=None):
    # [단어] = 강조색(빡이사식 단어 단위 색). stroke 0 이면 테두리·그림자 없이(흰 바탕 선화용)
    import re as _re
    x, y = xy
    parts = [p for p in _re.split(r"(\[[^\]]*\])", text) if p]
    for part in parts:
        hi = part.startswith("[")
        s = part.strip("[]")
        col = (accent or fill) if hi else fill
        if stroke:
            d.text((x + 6, y + 8), s, font=font, fill=(0, 0, 0, 160), stroke_width=stroke, stroke_fill=(0, 0, 0, 160))
            d.text((x, y), s, font=font, fill=col, stroke_width=stroke, stroke_fill=(0, 0, 0))
        else:
            d.text((x, y), s, font=font, fill=col)
        x += font.getlength(s)


def plain(text):
    return text.replace("[", "").replace("]", "")


def app_tile(c, size):
    # 앱 아이콘 한 장: 둥근 판 + 로고(위) + 이름(아래)
    S = size; t = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(t)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.22), fill=tuple(c["bg"]) + (255,))
    hl = Image.new("RGBA", (S, S), (0, 0, 0, 0))   # 위쪽 광택
    ImageDraw.Draw(hl).rounded_rectangle([0, 0, S - 1, int(S * 0.5)], radius=int(S * 0.22), fill=(255, 255, 255, 38))
    t = Image.alpha_composite(t, hl)
    logo = Image.open(c["logo"]).convert("RGBA"); logo = logo.crop(logo.getbbox())
    if c.get("logo_color"):                       # 단색 로고 색 바꾸기(검정 판 위 흰 로고 등)
        solid = Image.new("RGBA", logo.size, tuple(c["logo_color"]) + (255,)); solid.putalpha(logo.getchannel("A")); logo = solid
    ls = int(S * c.get("logo_scale", 0.5)); logo.thumbnail((ls, ls), Image.LANCZOS)
    t.alpha_composite(logo, ((S - logo.width) // 2, int(S * 0.36) - logo.height // 2))
    fn = fit_font(HEAD, c["name"], int(S * 0.84), int(S * 0.17)); tw = fn.getlength(c["name"])
    ImageDraw.Draw(t).text(((S - tw) // 2, int(S * 0.70)), c["name"], font=fn, fill=tuple(c.get("name_color", [20, 20, 20])))
    return t


def draw_fan(img, f):
    # 아이콘 카드 펼치기: 왼쪽·오른쪽은 기울여 뒤에, 가운데는 똑바로 앞에(출력 px)
    S = f.get("size", 190); cx, cy = f["x"], f["y"]; dx, dy, ang = f.get("dx", 140), f.get("dy", 30), f.get("angle", 15)
    cards = f["cards"]   # [왼, 가운데, 오른]
    boxes = []
    for c, (ox, oy, a) in [(cards[0], (-dx, dy, ang)), (cards[2], (dx, dy, -ang)), (cards[1], (0, 0, 0))]:
        t = app_tile(c, S); pad = 40
        base = Image.new("RGBA", (S + pad * 2, S + pad * 2), (0, 0, 0, 0))
        sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([pad + 6, pad + 14, pad + S + 6, pad + S + 14], radius=int(S * 0.22), fill=(0, 0, 0, 170))
        base = Image.alpha_composite(base, sh.filter(ImageFilter.GaussianBlur(12)))
        base.alpha_composite(t, (pad, pad))
        r = base.rotate(a, resample=Image.BICUBIC, expand=True)
        px0, py0 = int(cx + ox - r.width / 2), int(cy + oy - r.height / 2)
        img.alpha_composite(r, (px0, py0))
        bb = r.getchannel("A").point(lambda v: 255 if v > 200 else 0).getbbox()   # 그림자 빼고 카드만
        boxes.append((px0 + bb[0], py0 + bb[1], px0 + bb[2], py0 + bb[3]))
    for kx0, ky0, kx1, ky1 in f.get("keep_clear", []):   # 그림 속 화살표 등 가리면 안 되는 자리(출력 px)
        for bx0, by0, bx1, by1 in boxes:
            if bx0 < kx1 and kx0 < bx1 and by0 < ky1 and ky0 < by1:
                sys.exit(f"ERROR 겹침: 아이콘 카드 {(bx0, by0, bx1, by1)} 가 가리면 안 되는 자리 {(kx0, ky0, kx1, ky1)} 를 덮는다(10-15 «화살표 레이아웃 겹침 안 가려지게해»)")
    return img


def main():
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    src = Image.open(spec["scene"]).convert("RGB")
    for s in spec.get("screens", []):
        draw_screen(src, s["box"], s["lines"], s.get("size"))
    for tb in spec.get("tables", []):
        draw_table(src, tb["box"], tb.get("title"), tb["rows"], tb.get("total"), tb.get("size"))
    for lb in spec.get("labels", []):          # 그림 속 기존 말풍선 자리에 글만 바꿔 넣기(원본 px)
        x0, y0, x1, y1 = lb["box"]; dd = ImageDraw.Draw(src)
        dd.rounded_rectangle(lb["box"], radius=(y1 - y0) // 2, fill=tuple(lb.get("bg", [234, 235, 239])))
        fl = fit_font(UI, lb["text"], x1 - x0 - 16, int((y1 - y0) * 0.7))
        dd.text((x0 + 10, y0 + (y1 - y0 - fl.getbbox(lb["text"])[3]) // 2), lb["text"], font=fl, fill=(40, 40, 40))
    sw = src.width; ch = int(sw * 9 / 16); cy = spec.get("crop_y", 0)
    img = src.crop((0, cy, sw, cy + ch)).resize((W, H), Image.LANCZOS).convert("RGBA")
    # 아래로 어두워지는 받침(단색 판 아님)
    grad = Image.new("L", (1, H))
    for y in range(H):
        t = max(0.0, (y - H * 0.42) / (H * 0.58))
        grad.putpixel((0, y), int(230 * min(1.0, t * 1.15)))
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 255)); shade.putalpha(grad.resize((W, H)))
    img = Image.alpha_composite(img, shade)
    if spec.get("fan"):
        img = draw_fan(img, spec["fan"])
    ov =Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    if spec.get("shade", True) is False:
        img = Image.open(spec["scene"]).convert("RGB")
        img = img.crop((0, cy, sw, cy + ch)).resize((W, H), Image.LANCZOS).convert("RGBA")
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    if spec.get("arrow"):
        ax, ay = spec["arrow"]["x"], spec["arrow"]["y"]
        pts = [(ax - 70, ay - 22), (ax + 10, ay - 22), (ax + 10, ay - 50), (ax + 75, ay), (ax + 10, ay + 50), (ax + 10, ay + 22), (ax - 70, ay + 22)]
        d.polygon([(x + 4, y + 6) for x, y in pts], fill=(0, 0, 0, 140))
        d.polygon(pts, fill=(235, 30, 30, 255), outline=(255, 255, 255, 255), width=4)
    max_w = spec.get("max_w", W - MARGIN * 2)   # 얼굴을 피하려면 글자 폭 제한(출력 px)
    tc = tuple(spec.get("text_color", COLORS["white"])); ac = tuple(spec.get("accent", COLORS["yellow"]))
    st = spec.get("stroke", 8)
    f1 = fit_font(HEAD, plain(spec["line1"]), max_w, spec.get("size1", 104))
    f2 = fit_font(HEAD, plain(spec["line2"]), max_w, spec.get("size2", 132))
    h2 = f2.getbbox(plain(spec["line2"]))[3]; h1 = f1.getbbox(plain(spec["line1"]))[3]
    y2 = H - 40 - h2; y1 = y2 - 18 - h1
    l2c = COLORS[spec["line2_color"]] if spec.get("line2_color") else tc
    outlined(d, (MARGIN, y1), spec["line1"], f1, tc, stroke=st, accent=ac)
    outlined(d, (MARGIN, y2), spec["line2"], f2, l2c, stroke=int(st * 1.25), accent=ac)
    for tg in spec.get("tags", []):            # 꼬리표·이름표(채운 둥근 판 + 글자)
        ft = ImageFont.truetype(HEAD, tg.get("size", 40)); tw = ft.getlength(tg["text"]); th = ft.getbbox(tg["text"])[3]
        px, py = 18, 10; x0, y0 = tg["x"], tg["y"]
        d.rounded_rectangle([x0, y0, x0 + tw + px * 2, y0 + th + py * 2], radius=12, fill=tuple(tg.get("bg", [0, 0, 0])) + (255,))
        d.text((x0 + px, y0 + py - 2), tg["text"], font=ft, fill=tuple(tg.get("color", [255, 255, 255])))
    if spec.get("bubble"):                     # 말풍선(흰 판 + 꼬리)
        sys.exit("ERROR 말풍선 금지(10-15 사장님 «말풍선으로 표현하지마 말풍선 너 엄청못그려») — 덧말은 tags(채운 꼬리표)로")
        b = spec["bubble"]; fb = ImageFont.truetype(HEAD, b.get("size", 42)); tw = fb.getlength(b["text"]); th = fb.getbbox(b["text"])[3]
        x0, y0 = b["x"], b["y"]; x1, y1b = x0 + tw + 44, y0 + th + 30
        d.rounded_rectangle([x0, y0, x1, y1b], radius=26, fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=4)
        tx = b.get("tail_x", x0 + 40)
        d.polygon([(tx, y1b - 4), (tx + 34, y1b - 4), (tx + 8, y1b + 30)], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
        d.line([(tx + 2, y1b - 2), (tx + 32, y1b - 2)], fill=(255, 255, 255, 255), width=6)
        d.text((x0 + 22, y0 + 13), b["text"], font=fb, fill=(20, 20, 20))
    for rk in spec.get("marks", []):           # 빨간 네모 표시(출력 px) — «이 줄»이 가리키는 곳(10-23)
        d.rounded_rectangle(rk["box"], radius=10, outline=tuple(rk.get("color", [255, 40, 40])) + (255,), width=rk.get("width", 7))
    if spec.get("border"):
        bw = spec["border"].get("width", 14)
        d.rectangle([0, 0, W - 1, H - 1], outline=tuple(spec["border"]["color"]) + (255,), width=bw)   # 바깥 끝에 틈 없이(PIL 은 안쪽으로 두께를 그린다)
    if spec.get("inner"):
        i = spec["inner"]; fi = ImageFont.truetype(HAND, i.get("size", 46))
        d.text((i["x"] + 3, i["y"] + 4), i["text"], font=fi, fill=(0, 0, 0, 200), stroke_width=5, stroke_fill=(0, 0, 0, 200))
        d.text((i["x"], i["y"]), i["text"], font=fi, fill=(255, 255, 255), stroke_width=5, stroke_fill=(0, 0, 0))
    out = Image.alpha_composite(img, ov).convert("RGB")
    os.makedirs(os.path.dirname(spec["out"]), exist_ok=True)
    out.save(spec["out"], quality=92)
    out.resize((320, 180), Image.LANCZOS).save(os.path.splitext(spec["out"])[0] + "_모바일확인.jpg", quality=90)
    print(spec["out"])


if __name__ == "__main__":
    main()

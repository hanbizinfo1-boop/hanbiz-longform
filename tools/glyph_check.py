# -*- coding: utf-8 -*-
"""글꼴에 없는 글자(빈칸·네모로 찍히는 것)를 렌더 전에 잡는다.

사장님 10-08 13 «왼쪽 상단엔 글자도 깨지고» · 20 개구 «·»«→» 빈칸 · 19 Noto «▾» 네모 — 알던 함정을 또 밟아서 기계로 막는다.

    from glyph_check import check
    check("디자인, 글 배치", str(config.FONTS["gaegu_bold"]))   # config = tools/config.py   # 없는 글자가 있으면 SystemExit

    python glyph_check.py <글꼴> <글>        # 손으로 확인
"""
import sys
from functools import lru_cache

from fontTools.ttLib import TTFont


@lru_cache(maxsize=32)
def _cmap(path):
    f = TTFont(path, fontNumber=0, lazy=True)
    cm = set()
    for t in f["cmap"].tables:
        cm.update(t.cmap.keys())
    return frozenset(cm)


def missing(text, font_path):
    cm = _cmap(str(font_path))
    return sorted({ch for ch in text if not ch.isspace() and ord(ch) not in cm})


def check(text, font_path):
    m = missing(text, font_path)
    if m:
        raise SystemExit(f"글꼴에 없는 글자 {''.join(m)!r} — «{text}» ({font_path}). 다른 글자·선으로 바꾼다(후킹애펙-워크플로우 5장)")
    return text


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    m = missing(sys.argv[2], sys.argv[1])
    print("없는 글자:", "".join(m) if m else "없음")

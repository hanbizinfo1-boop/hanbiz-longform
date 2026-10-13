# -*- coding: utf-8 -*-
"""cards.html 의 #id 마다 투명 PNG(2배 해상도)로 찍는다 → 소재/pc/cards/<id>.png"""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[3]
html = (Path(__file__).parent / "html" / "cards.html").as_uri()
out = ROOT / "소재" / "pc" / "cards"; out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")   # 설치된 크롬 사용(브라우저 내려받기 없이)
    pg = b.new_page(device_scale_factor=2, viewport={"width": 1400, "height": 2400})
    pg.goto(html); pg.wait_for_timeout(500)
    for i in ["tg", "kk", "cal", "kk2", "buy"]:
        pg.locator(f"#{i}").screenshot(path=str(out / f"{i}.png"), omit_background=True)
        print(i)
    b.close()

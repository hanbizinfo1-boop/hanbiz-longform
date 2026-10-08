# -*- coding: utf-8 -*-
r"""확정본 위에 «얹을 것만» 담은 XML — 사장님 시퀀스(V1~V3·마스크)는 건드리지 않는다.

    python overlay_xml.py <map.json> <강조 placements.json> <강조 png폴더> <카드 segments.json> <카드영상폴더> <효과음폴더> <출력.xml>

카드 segments 자리에 side_panel_place.py 의 panels_place.json 을 주면 «보조 패널» 판(카드영상폴더 = 패널 PNG 폴더)
트랙 (XML 안):  V1 자료 카드 영상(카드+원형 PIP 합성) 또는 보조 패널 PNG  ·  V2~ 강조 네모/타원 PNG(쌓이는 만큼 트랙)  ·  A1 효과음
→ 프리미어: 이 시퀀스를 열어 전체 복사 → 사장님 시퀀스에서 **V4·A2 를 대상 트랙으로** 두고 0초에 붙여넣기
   (그러면 카드 V4 · 강조 V5 · 효과음 A2)
효과음 규칙(8강 문법): 타원·핵심 한 문장 = 도장 / 표·카드 속 항목 = 마우스클릭 / 그 밖 강조 = 띠딩2 /
   카드 첫 등장 = 종이소리 / 카드 항목 추가 = 띠딩2.  0.35초 안에 겹치면 앞의 것만.
강조 PNG 는 3프레임 페이드인 (8강의 세로 팝은 전체화면 PNG 에선 중심이 틀어져 못 옮긴다)
"""

import json
import sys
import wave
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape

FPS = 60000 / 1001
RATE = "<rate><timebase>60</timebase><ntsc>TRUE</ntsc></rate>"
TABLE_SLIDES = {3, 8, 17}
STATEMENT_SLIDES = {2, 9, 10, 12, 13, 19}


def url(p):
    s = str(Path(p).resolve()).replace("\\", "/")
    return "file://localhost/" + quote(s, safe="/:")


def fr(t):
    return int(round(t * FPS))


def vfile(fid, p, dur_s, first, w=1920, h=1080):
    if not first:
        return f'<file id="{fid}"/>'
    return (f'<file id="{fid}"><name>{escape(Path(p).name)}</name><pathurl>{escape(url(p))}</pathurl>{RATE}'
            f'<duration>{fr(dur_s)}</duration><media><video><samplecharacteristics>{RATE}'
            f'<width>{w}</width><height>{h}</height><pixelaspectratio>square</pixelaspectratio>'
            f'</samplecharacteristics></video></media></file>')


def afile(fid, p, first):
    if not first:
        return f'<file id="{fid}"/>'
    w = wave.open(str(p))
    dur = w.getnframes() / w.getframerate()
    return (f'<file id="{fid}"><name>{escape(Path(p).name)}</name><pathurl>{escape(url(p))}</pathurl>{RATE}'
            f'<duration>{fr(dur)}</duration><media><audio><samplecharacteristics><depth>16</depth>'
            f'<samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount>'
            f'</audio></media></file>'), dur


FADE = ("<filter><effect><name>Opacity</name><effectid>opacity</effectid><effectcategory>motion</effectcategory>"
        "<effecttype>motion</effecttype><mediatype>video</mediatype>"
        '<parameter authoringApp="PremierePro"><parameterid>opacity</parameterid><name>opacity</name>'
        "<valuemin>0</valuemin><valuemax>100</valuemax>"
        "<keyframe><when>0</when><value>0</value></keyframe><keyframe><when>3</when><value>100</value></keyframe>"
        "</parameter></effect></filter>")


def main():
    m = json.load(open(sys.argv[1], encoding="utf-8"))
    emp = json.load(open(sys.argv[2], encoding="utf-8"))
    pdir = Path(sys.argv[3])
    segs = json.load(open(sys.argv[4], encoding="utf-8"))
    cdir, sdir, out = Path(sys.argv[5]), Path(sys.argv[6]), Path(sys.argv[7])
    total = fr(m["duration"])
    sfx = {k: next(sdir.glob(f"{k}_*.wav")) for k in ("띠딩2", "도장", "마우스클릭", "종이소리", "뿅")}

    v1, cues = [], []
    v2 = [[]]            # 강조는 같은 화면에서 쌓이므로 시간이 겹친다 → 겹치면 윗 트랙으로
    ends = [0]
    if segs and "sfx" in segs[0]:
        # 보조 패널(side_panel_place.py) — 인물 전체화면 옆에 얹는 투명 PNG. 단계가 바뀌면 다음 PNG 로 이어진다
        for i, s in enumerate(segs, 1):
            a, b = fr(s["t0"]), fr(s["t1"])
            if b <= a:
                continue
            v1.append(f'<clipitem id="card{i}"><name>{escape(s["file"])}</name>{RATE}<start>{a}</start><end>{b}</end>'
                      f'<in>0</in><out>{b - a}</out><enabled>TRUE</enabled>'
                      + vfile("fc%d" % i, cdir / s["file"], 3600, True) + (FADE if s["fade"] else "") + '</clipitem>')
            if s["sfx"]:
                cues.append((s["t0"], s["sfx"], f"패널 {s['card']:02d} " + ("등장" if s["sfx"] == "종이소리" else "항목")))
    else:
        for i, s in enumerate(segs, 1):
            a, b = fr(s["t0"]), fr(s["t1"])
            v1.append(f'<clipitem id="card{i}"><name>{escape(s["file"])}</name>{RATE}<start>{a}</start><end>{b}</end>'
                      f'<in>0</in><out>{b - a}</out><enabled>TRUE</enabled>'
                      + vfile("fc%d" % i, cdir / s["file"], s["rendered"], True) + '</clipitem>')
            cues.append((s["t0"], "종이소리", f"카드 {s['card']:02d} 등장"))
        # 카드 항목 추가 시각
        plan = {(p["t0"], p["card"]): p for p in json.load(open(cdir.parent / "card_plan_final.json", encoding="utf-8"))}
        for (t0, card), p in plan.items():
            for st in p["steps"][1:]:
                if st - t0 > 0.35:
                    cues.append((st, "띠딩2", f"카드 {card:02d} 항목"))

    for e in emp:
        a, b = fr(e["t_in"]), fr(e["t_out"])
        if b - a < 3:
            continue
        k = next((j for j, en in enumerate(ends) if en <= a), None)
        if k is None:
            v2.append([]); ends.append(0); k = len(ends) - 1
        ends[k] = b
        v2[k].append(f'<clipitem id="em{e["no"]}"><name>{escape(e["png"])}</name>{RATE}<start>{a}</start><end>{b}</end>'
                  f'<in>0</in><out>{b - a}</out><enabled>TRUE</enabled>'
                  + vfile("fe%d" % e["no"], pdir / e["png"], 3600, True) + FADE + '</clipitem>')
        kind = ("도장" if e["shape"] == "ellipse" or e["slide"] in STATEMENT_SLIDES
                else "마우스클릭" if e["slide"] in TABLE_SLIDES else "띠딩2")
        cues.append((e["t_in"], kind, f"강조 {e['no']:02d} «{e['text']}»"))

    cues.sort()
    kept = []
    for c in cues:
        if kept and c[0] - kept[-1][0] < 0.35:
            continue
        kept.append(c)
    a1, aends, seen = [[]], [0], set()   # 효과음도 앞 소리가 안 끝났으면 다음 트랙으로
    for i, (t, kind, why) in enumerate(kept, 1):
        p = sfx[kind]
        first = kind not in seen
        seen.add(kind)
        fx = afile(f"fs_{kind}", p, True)
        fel, dur = fx if isinstance(fx, tuple) else (fx, 1.0)
        if not first:
            fel = f'<file id="fs_{kind}"/>'
        a = fr(t)
        n = fr(dur)
        k = next((j for j, en in enumerate(aends) if en <= a), None)
        if k is None:
            a1.append([]); aends.append(0); k = len(aends) - 1
        aends[k] = a + n
        a1[k].append(f'<clipitem id="sfx{i}"><name>{escape(p.name)}</name>{RATE}<start>{a}</start><end>{a + n}</end>'
                  f'<in>0</in><out>{n}</out><enabled>TRUE</enabled>{fel}'
                  f'<sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack></clipitem>')

    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="4">\n'
           f'<sequence id="seq_overlay"><name>{escape(out.stem)}</name><duration>{total}</duration>{RATE}'
           f'<timecode>{RATE}<string>00:00:00:00</string><frame>0</frame><displayformat>NDF</displayformat></timecode>'
           '<media><video><format><samplecharacteristics>'
           f'{RATE}<width>1920</width><height>1080</height><pixelaspectratio>square</pixelaspectratio>'
           '</samplecharacteristics></format>'
           '<track>' + "".join(v1) + '</track>' + "".join('<track>' + "".join(t) + '</track>' for t in v2)
           + '</video>'
           '<audio><format><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate>'
           '</samplecharacteristics></format>' + "".join('<track>' + "".join(t) + '</track>' for t in a1)
           + '</audio></media></sequence></xmeml>\n')
    out.write_text(xml, encoding="utf-8")
    (out.with_suffix(".효과음목록.txt")).write_text(
        "\n".join(f"{t:8.2f}  {k:6s}  {w}" for t, k, w in kept) + "\n", encoding="utf-8")
    print(f"카드 {len(v1)} · 강조 {sum(len(t) for t in v2)}(트랙 {len(v2)}) · 효과음 {sum(len(t) for t in a1)}(트랙 {len(a1)}) (겹쳐서 뺀 것 {len(cues) - len(kept)}) · 길이 {total}프레임")
    print(f"저장: {out}")


if __name__ == "__main__":
    sys.exit(main())

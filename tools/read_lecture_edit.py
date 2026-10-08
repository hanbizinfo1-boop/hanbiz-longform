# -*- coding: utf-8 -*-
r"""강의 편집본 prproj 를 트랙 단위로 전수 읽는다. 읽기 전용.

사장님이 강의를 «어떻게» 편집했는지 — 트랙마다 무엇을 깔고, 어떤 이펙트를 걸고,
그래픽에 무슨 글자를 어떤 글꼴로 썼고, 효과음을 어디 붙였고, 자막을 어떻게 넣었는지 —
를 한 JSON 으로 뽑는다.

    python read_lecture_edit.py <prproj> <시퀀스이름> <출력.json>

구조 (창근님.prproj 8강에서 실측)
    Sequence → TrackGroups/TrackGroup/Second
        → VideoTrackGroup / AudioTrackGroup / DataTrackGroup(캡션)
        → Tracks/Track(ObjectURef) → *ClipTrack → TrackItem(ObjectRef)
    VideoClipTrackItem → Components → VideoComponentChain → Component(ObjectRef)
        → VideoFilterComponent (MatchName, DisplayName, Params → *ComponentParam)
    CaptionDataClipTrackItem → BlockVector → Block → FormattedTextData(base64)
"""

import base64
import gzip
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TICKS = 254016000000
NOKEY = -91445760000000000          # «키프레임 없음» 표시값
KO = re.compile(r"[가-힣0-9A-Za-z(][가-힣0-9A-Za-z ,.!?~·%()\-=→÷×+:/'\"]*[가-힣0-9A-Za-z!?%)]")
FONT = re.compile(r"[A-Z][A-Za-z0-9]{3,}(?:-[A-Za-z]+)?")
NOT_FONT = {"AnimationType"}   # 블롭 안의 필드 이름


def load(p):
    with gzip.open(p, "rb") as f:
        return ET.fromstring(f.read())


class Proj:
    def __init__(self, root):
        self.by_id, self.by_uid = {}, {}
        for el in root.iter():
            i, u = el.get("ObjectID"), el.get("ObjectUID")
            if i:
                self.by_id[i] = el
            if u:
                self.by_uid[u] = el

    def d(self, el):
        if el is None:
            return None
        r, u = el.get("ObjectRef"), el.get("ObjectURef")
        if r:
            return self.by_id.get(r)
        if u:
            return self.by_uid.get(u)
        return None


def sec(v):
    return round(int(v) / TICKS, 3)


def blob_strings(b64):
    """base64 블롭 안의 사람이 읽을 문자열(한글 문구·글꼴 이름)."""
    try:
        raw = base64.b64decode(b64)
    except Exception:
        return [], []
    txt = raw.decode("utf-8", "ignore")
    texts = [s for s in KO.findall(txt) if re.search("[가-힣]", s)]
    fonts = sorted(set(FONT.findall(txt)) - NOT_FONT)
    return texts, fonts


def param_value(p):
    """정적 값과 키프레임 수. StartKeyframe 의 첫 필드가 시각, 둘째가 값."""
    sk = p.findtext("StartKeyframe") or ""
    parts = sk.split(",")
    val = parts[1] if len(parts) > 1 else (p.findtext("CurrentValue") or "")
    keys = []
    kfs = (p.findtext("Keyframes") or "").strip()
    for k in filter(None, kfs.split(";")):
        f = k.split(",")
        try:
            keys.append([round(int(f[0]) / TICKS, 3), f[1]])
        except (ValueError, IndexError):
            pass
    return val, keys


def components(pj, item):
    out, texts, fonts = [], [], []
    ch = pj.d(item.find(".//Components"))
    if ch is None:
        return out, texts, fonts
    for c in ch.iter("Component"):
        ce = pj.d(c)
        if ce is None:
            continue
        # 오디오 필터는 AudioComponent 한 겹 안쪽에 Component 가 있다
        comp = ce.find("Component")
        if comp is None:
            comp = ce.find("AudioComponent/Component")
        name = comp.findtext("DisplayName") if comp is not None else ""
        name = name or ce.findtext("FilterMatchName") or ""
        params = {}
        if comp is not None:
            for q in comp.iter("Param"):
                pe = pj.d(q)
                if pe is None:
                    continue
                pn = pe.findtext("Name") or f"#{pe.findtext('ParameterID')}"
                val, keys = param_value(pe)
                # 키프레임이 있으면 [시각(초, 미디어 기준), 값] 목록을 같이 남긴다
                params[pn] = {"v": val[:60], "kf": len(keys), "keys": keys} if keys else val[:60]
                # 텍스트 레이어는 소스 텍스트 파라미터 안 블롭에 글자와 글꼴이 든다
                for el in pe.iter():
                    t = (el.text or "").strip()
                    if len(t) > 60 and re.fullmatch(r"[A-Za-z0-9+/=\s]+", t):
                        tx, fo = blob_strings(t)
                        texts += [s for s in tx if s not in texts]
                        fonts += [f for f in fo if f not in fonts]
        out.append({"match": ce.findtext("MatchName") or ce.tag,
                    "name": name, "params": params})
    return out, texts, fonts


def media_name(pj, item):
    sub = pj.d(item.find(".//SubClip"))
    if sub is None:
        return None, None, None
    nm = sub.findtext("Name")
    clip = pj.d(sub.find("Clip"))
    ip = clip.findtext(".//InPoint") if clip is not None else None
    op = clip.findtext(".//OutPoint") if clip is not None else None
    return nm, (sec(ip) if ip else None), (sec(op) if op else None)


def item_times(item):
    ti = item.find(".//TrackItem")
    s = (ti.findtext("Start") if ti is not None else None) or "0"
    e = ti.findtext("End") if ti is not None else None
    return sec(s), (sec(e) if e else None)


def read_track(pj, track, kind, idx):
    rows = []
    for x in track.iter("TrackItem"):
        it = pj.d(x)
        if it is None:
            continue
        t0, t1 = item_times(it)
        if t1 is None:
            continue
        row = {"track": f"{kind}{idx}", "type": it.tag, "t0": t0, "t1": t1}
        if it.tag.endswith("TransitionTrackItem"):
            tt = it.find("TransitionTrackItem")
            row["name"] = tt.findtext("DisplayName") if tt is not None else ""
            row["match"] = tt.findtext("MatchName") if tt is not None else ""
        elif it.tag == "CaptionDataClipTrackItem":
            texts, fonts = [], []
            for b in it.iter("BlockVectorItem"):
                be = pj.d(b)
                if be is None:
                    continue
                tx, fo = blob_strings(be.findtext("FormattedTextData") or "")
                texts += tx
                fonts += [f for f in fo if f not in fonts]
            row["text"] = " ".join(texts)
            row["fonts"] = fonts
        else:
            nm, s0, s1 = media_name(pj, it)
            row.update(name=nm, s0=s0, s1=s1)
            comps, texts, fonts = components(pj, it)
            row["fx"] = comps
            if texts:
                row["text"] = texts
            if fonts:
                row["fonts"] = fonts
        rows.append(row)
    return rows


def main():
    src, want, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    root = load(src)
    pj = Proj(root)
    seqs = [el for el in root.iter("Sequence") if (el.findtext("Name") or "") == want]
    if not seqs:
        print(f"★ 시퀀스 «{want}» 를 못 찾았다")
        return 1

    def read_seq(seq):
        rows = []
        if seq.find("TrackGroups") is None:
            return rows
        for tg in seq.find("TrackGroups").iter("TrackGroup"):
            g = pj.d(tg.find("Second"))
            if g is None or g.find(".//Tracks") is None:
                continue
            kind = {"VideoTrackGroup": "V", "AudioTrackGroup": "A"}.get(g.tag, "C")
            for tr in g.find(".//Tracks"):
                t = pj.d(tr)
                if t is None:
                    continue
                rows += read_track(pj, t, kind, int(tr.get("Index")) + 1)
        return rows

    # 같은 이름 시퀀스가 여럿일 수 있다(09-30 강의13 자동저장: 빈 껍데기가 뒤에 있었다) → 아이템이 가장 많은 것
    rows = max((read_seq(s) for s in seqs), key=len)

    rows.sort(key=lambda r: (r["track"], r["t0"]))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"project": str(src), "sequence": want, "items": rows},
                              ensure_ascii=False, indent=1), encoding="utf-8")

    from collections import Counter
    c = Counter((r["track"], r["type"]) for r in rows)
    print(f"{src.name} «{want}» — 아이템 {len(rows)}개")
    for (tr, ty), n in sorted(c.items()):
        print(f"  {tr:4s} {ty:28s} {n:5d}")
    print(f"저장: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

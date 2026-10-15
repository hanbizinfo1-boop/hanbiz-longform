"""템플릿 서랍 등록기 — templates/*/template.json 을 읽어 검사하고 목록·카탈로그를 만든다.

실행:  python tools/auto/registry.py
만드는 것:
  templates/registry.json   통과한 템플릿 목록(③짜기가 읽는다)
  templates/카탈로그.md      사람이 보는 표 — 교차표 + 단계별 · 연출 주체별 · 도구별 세 갈래 표
ERROR 가 난 템플릿은 목록에서 뺀다(카탈로그 맨 위 «거절됨» 표에 이유). WARN 은 목록에 남긴다.
허용 목록은 templates/README.md 와 같게 아래 상수로 둔다(README 를 파싱하지 않는다 — README 를 고치면 여기도 고친다).
손으로 registry.json·카탈로그.md 를 고치지 않는다.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TPL_DIR = ROOT / "templates"

# ── README 와 같게 유지하는 허용 목록 ─────────────────────────────
DRAWERS = ["GU", "CA", "EM", "SC", "TR", "OE", "SD"]            # 1장 (TN 은 tones/ 에 따로)
DRAWER_NAMES = {"GU": "구성 틀", "CA": "카메라", "EM": "강조", "SC": "장면", "TR": "전환·표지", "OE": "오프닝·엔딩", "SD": "소리"}
STATUSES = ["통과", "대기", "시안", "신규", "폐기"]                # 폐기 = 사장님 금지에 걸려 고르지 않음(banned_reason 필수)                      # 2장 status
# (ae 는 10-13 에 뺐다 — After Effects 를 새 작업에 안 쓴다. 옛 판은 template.json 의 engine_from 에만 남는다)
ENGINES = ["html", "pil", "design", "blender", "aivideo", "compose"]
SUBJECTS = ["사람", "녹화화면", "글자", "자료이미지", "캐릭터", "데이터", "무대배경", "브랜드", "소리"]   # 2장 subject
TAGS = {                                                         # 3장
    "설정·버튼", "화면 속 특정 부분", "개념 비교", "과정·단계", "보는 사람 시점", "일상 상황", "현실 공간·사람",
    "정리·목차", "숫자·금액", "용어 제시", "질문", "경고·실수", "사례·후기", "알고리즘·시스템 행동",
    "소개·여러 항목", "결론·센 말", "챕터 시작", "챕터 끝", "한 편 시작", "한 편 끝", "자료 등장", "브랜드", "감정·리액션", "가림",
    "리스트", "부연", "정의·조건", "수식",                        # 강의 6유형 (용어 제시·질문은 위에 이미 있음)
}
IMAGE_SOURCES = {"doc", "codex", "crawl", "real_capture", "brand", "char2d", "render3d", "aivideo"}   # 4장
IMAGE_STYLES = {"실사 사진", "2D 플랫", "3D 비닐", "손글씨 종이"}
SLOT_KINDS = {"text", "image", "box", "words", "number", "choice"}
DRAWN_ALLOWED = {"차트",                                                 # 5장
    "카드바탕", "판", "구분선", "테두리", "밑줄", "타원테두리", "형광펜", "말풍선바탕", "효과선", "반짝선",
    "테두리번짐", "빛훑기", "어둡게덮기", "UI위젯", "HUD", "글자",
}
LAYERS = {"L1", "L2", "L4", "L5", "audio"}
SCREENS = {"PIP", "풀샷", "사람없음"}
TONES = ["TN-1", "TN-2", "TN-3", "TN-4"]
EASES = {"eo", "ez", "lin", "hold"}
REQUIRED = ["id", "name", "drawer", "version", "status", "engine", "subject", "summary", "use_when", "screens", "layer",
            "duration", "slots", "drawn_allowed", "timeline", "sfx", "rules", "fallback", "from", "basis"]
ID_RE = re.compile(r"^(GU|CA|EM|SC|TR|OE|SD)-\d{2}$")


def is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def check(path, data):
    """(errors, warns) 반환."""
    errs, warns = [], []
    E, W = errs.append, warns.append
    if not isinstance(data, dict):
        return ["최상위가 객체가 아님"], []
    for k in REQUIRED:
        if k not in data:
            E(f"필수 필드 없음: {k}")
    tid = data.get("id")
    if "id" in data:
        if not isinstance(tid, str) or not ID_RE.match(tid):
            E(f"id 형식 오류: {tid!r} (예 CA-03)")
        else:
            fname = path.parent.name
            if not (fname == tid or fname.startswith(tid + "_")):
                E(f"폴더 이름 '{fname}' 이 id '{tid}' 로 시작하지 않음")
            if data.get("drawer") != tid[:2]:
                E(f"drawer '{data.get('drawer')}' 가 id 앞 '{tid[:2]}' 와 다름")
    if "status" in data and data["status"] not in STATUSES:
        E(f"status 오류: {data['status']!r} (통과·대기·시안·신규·폐기)")
    if "engine" in data and data["engine"] not in ENGINES:
        E(f"engine 오류: {data['engine']!r}")
    if "layer" in data and data["layer"] not in LAYERS:
        E(f"layer 오류: {data['layer']!r}")
    if "version" in data and not (isinstance(data["version"], int) and not isinstance(data["version"], bool) and data["version"] >= 1):
        E("version 은 1 이상 정수")
    for k in ("name", "summary", "from", "basis"):
        if k in data and not (isinstance(data[k], str) and data[k].strip()):
            E(f"{k} 가 비어 있음")

    # subject (필수) · source_ref (선택)
    sj = data.get("subject")
    if "subject" in data:
        if not isinstance(sj, list) or not sj:
            E("subject 는 비어 있지 않은 배열")
        else:
            bad = [x for x in sj if x not in SUBJECTS]
            if bad:
                E(f"subject 허용 목록 밖: {bad}")
            if len(sj) > 2:
                W(f"subject {len(sj)}개 — 연출 주체는 하나 또는 둘")
    if "source_ref" in data:
        sr = data["source_ref"]
        if not (isinstance(sr, list) and all(isinstance(x, str) and x.strip() for x in sr)):
            W("source_ref 는 문자열 배열이어야 함")

    # 상황 태그
    for k in ("use_when", "avoid_when"):
        if k in data:
            v = data[k]
            if not isinstance(v, list):
                E(f"{k} 는 배열")
            else:
                bad = [x for x in v if x not in TAGS]
                if bad:
                    E(f"{k} 에 3장 태그 밖의 말: {bad}")

    # screens
    if "screens" in data:
        v = data["screens"]
        if not isinstance(v, list) or not v or any(x not in SCREENS for x in v):
            E(f"screens 오류: {v!r} (PIP·풀샷·사람없음)")

    # tones
    if "tones" in data:
        t = data["tones"]
        if not isinstance(t, dict):
            E("tones 는 객체")
        else:
            for k, val in t.items():
                if k not in TONES:
                    E(f"tones 키 오류: {k}")
                elif not is_num(val) or not 0 <= val <= 1:
                    E(f"tones[{k}] 는 0~1 숫자: {val!r}")

    # duration
    if "duration" in data:
        d = data["duration"]
        if not (isinstance(d, list) and len(d) == 2 and all(is_num(x) for x in d) and 0 <= d[0] <= d[1]):
            E(f"duration 은 [최소, 최대] 숫자 (0 ≤ 최소 ≤ 최대): {d!r}")

    # drawn_allowed — 도형 흉내 방지
    if "drawn_allowed" in data:
        v = data["drawn_allowed"]
        if not isinstance(v, list):
            E("drawn_allowed 는 배열")
        else:
            bad = [x for x in v if x not in DRAWN_ALLOWED]
            if bad:
                E(f"drawn_allowed 가 5장 목록 밖 → 도형 흉내 의심: {bad}")

    # slots
    if "slots" in data:
        s = data["slots"]
        if not isinstance(s, dict):
            E("slots 는 객체")
        else:
            for name, sl in s.items():
                if not isinstance(sl, dict):
                    E(f"slots.{name} 가 객체가 아님")
                    continue
                kind = sl.get("kind")
                if kind not in SLOT_KINDS:
                    W(f"slots.{name}.kind '{kind}' 는 README 2장 종류 밖")
                if kind == "image":
                    src = sl.get("source")
                    if not isinstance(src, list) or not src:
                        E(f"slots.{name}: image 칸에 source 가 없음")
                    else:
                        bad = [x for x in src if x not in IMAGE_SOURCES]
                        if bad:
                            E(f"slots.{name}.source 4장 목록 밖: {bad}")
                    st = sl.get("style")
                    if st is not None and st not in IMAGE_STYLES:
                        W(f"slots.{name}.style '{st}' 는 4장 style 밖")

    # timeline
    if "timeline" in data:
        tl = data["timeline"]
        if not isinstance(tl, list) or not tl:
            E("timeline 은 비어 있지 않은 배열")
        else:
            for i, step in enumerate(tl):
                if not isinstance(step, dict) or "at" not in step or "do" not in step:
                    W(f"timeline[{i}] 에 at/do 없음")
                    continue
                if "ease" in step and step["ease"] not in EASES:
                    W(f"timeline[{i}].ease '{step['ease']}' 는 eo/ez/lin/hold 밖")

    # sfx / rules / fallback
    if "sfx" in data:
        if not isinstance(data["sfx"], list):
            E("sfx 는 배열")
        else:
            for i, s in enumerate(data["sfx"]):
                if not isinstance(s, dict) or "at" not in s or "role" not in s:
                    W(f"sfx[{i}] 에 at/role 없음")
                elif s.get("meaning") not in ("긍정", "부정", "중립", "그림", None):
                    W(f"sfx[{i}].meaning '{s.get('meaning')}' 는 긍정/부정/중립 밖")
    if "rules" in data:
        if not (isinstance(data["rules"], list) and data["rules"] and all(isinstance(x, str) for x in data["rules"])):
            E("rules 는 비어 있지 않은 문자열 배열(줄마다 끝에 근거)")
    if "fallback" in data and not (isinstance(data["fallback"], list) and all(isinstance(x, str) for x in data["fallback"])):
        E("fallback 은 ID 문자열 배열")
    return errs, warns


def tone_top(t):
    """느낌 가중치 상위 표시. 안 적었으면 모두 0.5(기본)라 «—»."""
    t = t or {}
    items = sorted(((k, v) for k, v in t.items() if k in TONES and is_num(v)), key=lambda kv: (-kv[1], kv[0]))
    top = [f"{k}:{v:g}" for k, v in items if v > 0.5][:2]
    low = [f"{k}:{v:g}" for k, v in reversed(items) if v < 0.5][:1]
    s = " · ".join(top)
    if low:
        s += (" / " if s else "") + "낮음 " + low[0]
    return s or "—"


def cell(x):
    if isinstance(x, list):
        x = ", ".join(str(i) for i in x)
    return ("—" if x in (None, "") else str(x)).replace("|", "/").replace("\n", " ")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    loaded, rejected, warn_all = [], [], []
    ids_seen = {}
    n_read = 0
    for p in sorted(TPL_DIR.glob("*/template.json")):
        n_read += 1
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:  # 깨진 JSON
            rejected.append({"folder": p.parent.name, "id": "?", "errors": [f"JSON 읽기 실패: {e}"]})
            continue
        errs, warns = check(p, data)
        tid = data.get("id") if isinstance(data, dict) else None
        loaded.append({"path": p, "data": data, "errs": errs, "warns": warns})
        if isinstance(tid, str):
            ids_seen.setdefault(tid, []).append(p.parent.name)
    # id 중복 — 둘 다 거절
    for rec in loaded:
        tid = rec["data"].get("id") if isinstance(rec["data"], dict) else None
        if isinstance(tid, str) and len(ids_seen.get(tid, [])) > 1:
            rec["errs"].append(f"id 중복: {tid} ← {', '.join(ids_seen[tid])}")
    good = []
    for rec in loaded:
        if rec["errs"]:
            rejected.append({"folder": rec["path"].parent.name, "id": (rec["data"].get("id") if isinstance(rec["data"], dict) else "?"), "errors": rec["errs"]})
        else:
            good.append(rec)
    good_ids = {r["data"]["id"] for r in good}
    for rec in good:
        d = rec["data"]
        for fb in d.get("fallback", []):
            if fb not in good_ids:
                rec["warns"].append(f"fallback '{fb}' 이(가) 아직 없음(또는 거절됨)")
        for w in rec["warns"]:
            warn_all.append((d["id"], w))

    good.sort(key=lambda r: r["data"]["id"])
    entries = []
    for rec in good:
        d = rec["data"]
        entries.append({
            "id": d["id"], "name": d["name"], "drawer": d["drawer"], "version": d["version"], "status": d["status"],
            "engine": d["engine"], "subject": d["subject"], "summary": d["summary"],
            "use_when": d.get("use_when", []), "avoid_when": d.get("avoid_when", []), "tones": d.get("tones", {}),
            "screens": d["screens"], "layer": d["layer"], "moves_person": d.get("moves_person", False),
            "duration": d["duration"], "fallback": d.get("fallback", []),
            "source_ref": d.get("source_ref", []), "folder": rec["path"].parent.name,
        })

    # ── 집계 ──
    by_drawer = {k: [e for e in entries if e["drawer"] == k] for k in DRAWERS}
    by_status = {s: [e for e in entries if e["status"] == s] for s in STATUSES}
    cross_subj = {k: {s: 0 for s in SUBJECTS} for k in DRAWERS}
    cross_eng = {k: {g: 0 for g in ENGINES} for k in DRAWERS}
    for e in entries:
        for s in e["subject"]:
            cross_subj[e["drawer"]][s] += 1
        cross_eng[e["drawer"]][e["engine"]] += 1

    reg = {
        "generated": date.today().isoformat(),
        "counts": {"total": len(entries), "rejected": len(rejected),
                   "by_drawer": {k: len(v) for k, v in by_drawer.items()},
                   "by_status": {k: len(v) for k, v in by_status.items()}},
        "templates": entries,
    }
    with open(TPL_DIR / "registry.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # ── 카탈로그.md ──
    L = []
    L.append("# 템플릿 카탈로그")
    L.append("")
    L.append(f"> `python tools/auto/registry.py` 가 만든다({reg['generated']}). 손으로 고치지 않는다. 규격은 `README.md`.")
    L.append(f"> 등록 {len(entries)}개 · 거절 {len(rejected)}개 · WARN {len(warn_all)}건")
    L.append("")
    if rejected:
        L.append("## 거절됨 (목록에서 뺐다)")
        L.append("")
        L.append("| 폴더 | ID | 이유 |")
        L.append("|---|---|---|")
        for r in rejected:
            L.append(f"| {cell(r['folder'])} | {cell(r['id'])} | {cell(' ; '.join(r['errors']))} |")
        L.append("")

    def cross(title, rows, cols, grid):
        L.append(f"## {title}")
        L.append("")
        L.append("| 서랍 | " + " | ".join(cols) + " | 합 |")
        L.append("|---|" + "---|" * (len(cols) + 1))
        for k in rows:
            row = [grid[k][c] for c in cols]
            L.append(f"| {k} {DRAWER_NAMES[k]} | " + " | ".join(str(x) if x else "·" for x in row) + f" | {sum(row) or '·'} |")
        tot = [sum(grid[k][c] for k in rows) for c in cols]
        L.append("| **합** | " + " | ".join(str(x) if x else "·" for x in tot) + f" | {sum(tot)} |")
        L.append("")

    L.append("# 한눈에 — 빈칸(·)이 아직 비어 있는 자리")
    L.append("")
    L.append("> 연출 주체가 둘인 템플릿은 두 열에 다 센다(그래서 합이 템플릿 수보다 클 수 있다).")
    L.append("")
    cross("서랍 × 연출 주체", DRAWERS, SUBJECTS, cross_subj)
    cross("서랍 × 도구(engine)", DRAWERS, ENGINES, cross_eng)
    L.append("## 상태별")
    L.append("")
    L.append("| " + " | ".join(STATUSES) + " |")
    L.append("|" + "---|" * len(STATUSES))
    L.append("| " + " | ".join(str(len(by_status[s])) for s in STATUSES) + " |")
    maker = [e for e in entries if e["engine"] not in ("ae", "blender") and e["status"] != "폐기"]
    L.append("")
    L.append(f"> **제작 컴퓨터(새 PC)에서 쓸 수 있는 것 {len(maker)}개** — 애프터이펙트 없음(10-13 «에펙말고 다른방향으로 연출해야해»). "
             f"`engine: ae` {sum(1 for e in entries if e['engine'] == 'ae')}개는 연출표에서 고르지 않고, 필요하면 html/compose 로 다시 만든다. blender 는 설치 확인 전까지 보류.")
    L.append("")

    def full_table(es):
        L.append("| ID | 이름 | 주체 | 상태 | 엔진 | 한 줄 | 쓰는 상황 | 피하는 상황 | 느낌 가중치 상위 | fallback |")
        L.append("|---|---|---|---|---|---|---|---|---|---|")
        for e in es:
            L.append("| " + " | ".join([e["id"], cell(e["name"]), cell(e["subject"]), e["status"], e["engine"], cell(e["summary"]),
                                        cell(e["use_when"]), cell(e["avoid_when"]), tone_top(e["tones"]), cell(e["fallback"])]) + " |")
        L.append("")

    def short_table(es):
        L.append("| ID | 이름 | 서랍 | 상태 | 엔진 | 주체 | 한 줄 | 느낌 가중치 상위 |")
        L.append("|---|---|---|---|---|---|---|---|")
        for e in es:
            L.append("| " + " | ".join([e["id"], cell(e["name"]), e["drawer"], e["status"], e["engine"], cell(e["subject"]),
                                        cell(e["summary"]), tone_top(e["tones"])]) + " |")
        L.append("")

    L.append("# ① 단계(서랍)별")
    L.append("")
    for k in DRAWERS:
        L.append(f"## {k} {DRAWER_NAMES[k]} ({len(by_drawer[k])})")
        L.append("")
        if by_drawer[k]:
            full_table(by_drawer[k])
        else:
            L.append("(아직 없음)")
            L.append("")
    L.append("# ② 연출 주체별")
    L.append("")
    for s in SUBJECTS:
        es = [e for e in entries if s in e["subject"]]
        L.append(f"## {s} ({len(es)})")
        L.append("")
        if es:
            short_table(es)
        else:
            L.append("(아직 없음)")
            L.append("")
    L.append("# ③ 도구(engine)별")
    L.append("")
    for g in ENGINES:
        es = [e for e in entries if e["engine"] == g]
        L.append(f"## {g} ({len(es)})")
        L.append("")
        if es:
            short_table(es)
        else:
            L.append("(아직 없음)")
            L.append("")
    with open(TPL_DIR / "카탈로그.md", "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L).rstrip("\n") + "\n")

    # ── 화면 ──
    print(f"템플릿 폴더: {TPL_DIR}")
    print(f"읽음 {n_read}개 → 등록 {len(entries)} · 거절 {len(rejected)}")
    if rejected:
        print("\n[거절됨 — ERROR]")
        for r in rejected:
            print(f"  {r['id']} ({r['folder']})")
            for m in r["errors"]:
                print(f"    ERROR {m}")
    if warn_all:
        print("\n[WARN]")
        for tid, w in warn_all:
            print(f"  {tid}: {w}")
    print("\n[서랍별 개수]")
    for k in DRAWERS:
        print(f"  {k} {DRAWER_NAMES[k]}: {len(by_drawer[k])}")
    print("[상태별 개수]")
    for s in STATUSES:
        print(f"  {s}: {len(by_status[s])}")
    print(f"\n쓴 파일: {TPL_DIR / 'registry.json'}, {TPL_DIR / '카탈로그.md'}")
    print(f"ERROR 템플릿 {len(rejected)}개 · WARN {len(warn_all)}건")
    return 1 if rejected else 0


if __name__ == "__main__":
    sys.exit(main())

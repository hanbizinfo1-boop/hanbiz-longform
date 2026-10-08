# -*- coding: utf-8 -*-
r"""효과음 찾기 — 파일 이름 일부·분류·뜻으로 효과음 폴더 전부를 뒤져 «어디 있는지 · 등급 · 구울 크기 · 사장님 통과 여부»를 한 줄씩 보여 준다.

    python tools/sfx_find.py 도장                 # 이름에 «도장» 이 든 파일(모든 폴더)
    python tools/sfx_find.py --cat 02             # 등급표 분류 02_뿅_팝 상위(A★→A→B)
    python tools/sfx_find.py --role stamp         # 뜻별 단골(references/sfx-workflow.md 3장 표와 같은 것)
    python tools/sfx_find.py --roles              # 뜻별 단골 표 전체
    python tools/sfx_find.py --dirs               # 효과음 폴더 지도(있는지·파일 수)
    python tools/sfx_find.py 휙 --play            # 첫 결과를 기본 플레이어로 열어 들어 본다

폴더 지도·찾는 순서는 config.SFX_ROOTS 한 곳. 크기는 bisa_meta_sfx.FILE_DB(표에 없으면 +5dB).
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402

AUDIO = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aif", ".aiff"}
ORDER = {"A★": 0, "A": 1, "B": 2, "C": 3, "-": 9}

# 뜻별 단골 — 빡이사DB 후킹 01~23 에서 실제로 쓰고 사장님이 남기신 소리. (파일, 최대 길이 초, 구울 dB, 맞춤)
# 최대 길이 음수 = 그 길이로 딱 자름(그리는 동작 길이에 맞출 때) · 맞춤 onset = 소리 시작을 그림 등장에 · peak = 소리 꼭대기를 움직임 꼭대기에(휙 계열)
ROLES = {
    "in":     ("휙２.mp3", 0.6, 4, "peak", "중립", "판·장면이 들어옴(확대·반반 갈림)"),
    "back":   ("휙1.mp3", 0.7, 8, "peak", "중립", "판이 빠지고 사람으로 돌아감"),
    "card":   ("ML_Cartoon bubbles popping.wav", 0.5, 5, "onset", "중립", "카드·칸·댓글이 쑥 나옴"),
    "st1":    ("KN_pepSound1.wav", 0.4, 8, "onset", "중립", "단계 알약·목록 줄(번갈아 st2)"),
    "st2":    ("KN_pepSound2.wav", 0.4, 8, "onset", "중립", "단계 알약·목록 줄(번갈아 st1)"),
    "big":    ("SEL_文字表示の衝撃音1.mp3", 0.8, 5, "onset", "중립", "큰 글 쿵(강조 자막) — 1·2·3 번갈아. 조건·기준 글에도 이것(축하음 금지)"),
    "ok":     ("맑은소리.mp3", 0.8, 7, "onset", "긍정", "잘 됨·정답·추천 ✓"),
    "no":     ("KN_error_003.wav", 0.5, 5, "onset", "부정", "안 됨·✕·지움·허수"),
    "miss":   ("KN_lowDown.wav", 0.8, 5, "onset", "부정", "실망·부재·내려감"),
    "stamp":  ("도장.mp3", 0.6, 5, "onset", "그림", "도장 그림엔 반드시 이것(10-08 사장님)"),
    "msg":    ("채팅 효과음.mp3", 0.6, 5, "onset", "그림", "문의·메시지·알림톡이 넘어감"),
    "bell":   ("ML_Bell notification.wav", 0.8, 5, "onset", "그림", "새 DB·알림 도착"),
    "ring":   ("SEL_携帯電話の着信音1.mp3", 1.2, 5, "onset", "그림", "전화 걸림"),
    "click":  ("마우스 클릭.mp3", 0.25, 5, "onset", "그림", "커서 누름(번갈아 «15. 마우스클릭.mp3»)"),
    "type":   ("SEL_キーボード2.mp3", 0.45, 6, "onset", "그림", "타자"),
    "pen":    ("SEL_シャーペンで字を書く.mp3", 0.8, 4, "onset", "그림", "노트 손글씨"),
    "marker": ("SEL_油性マーカーで字を書く.mp3", -0.35, 3, "onset", "그림", "동그라미·밑줄 긋기"),
    "page":   ("ML_Page turn chime.wav", 1.0, 5, "onset", "그림", "페이지·책 넘김"),
    "sweep":  ("ML_Fast sweep transition.wav", 0.6, 5, "onset", "중립", "자료 카드 날아듦(air·small 번갈아)"),
    "gauge":  ("SEL_ゲージ回復1.mp3", 0.6, 12, "onset", "긍정", "게이지·막대 차오름(1·2·3)"),
    "shine":  ("SEL_キラッ1.mp3", 0.7, -1, "onset", "긍정", "빛줄 훑기·핵심 반짝"),
    "level":  ("SEL_レベルアップ.mp3", 0.9, 5, "onset", "긍정", "단계 완주(4차 콜까지 등)"),
}


def file_db():
    try:
        import bisa_meta_sfx as S  # 무거운 import 가 실패해도 찾기는 되게
        return S.FILE_DB, S.FILE_DB_DEFAULT
    except Exception:
        return {}, 5


def load_json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return None


def index():
    grade = {Path(r["파일"]).name: r for r in (load_json(config.GRADE_JSON) or [])}
    used = load_json(config.USED_JSON) or {}
    ok, bad = set(used.get("통과", [])), set(used.get("반려", []))
    return grade, ok, bad


def walk():
    seen = set()
    for tag, root in config.SFX_ROOTS.items():
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if p.suffix.lower() in AUDIO and p.is_file() and "_청음" not in p.parts:
                key = (p.name, p.stat().st_size)
                if key not in seen:
                    seen.add(key)
                    yield tag, p


def row(tag, p, grade, ok, bad, fdb, dflt):
    g = grade.get(p.name, {})
    mark = "통과" if p.name in ok else ("반려" if p.name in bad else "")
    db = fdb.get(p.name, dflt)
    return f"[{tag:4}] {g.get('등급', '-'):2} {db:+3d}dB {mark:2} {g.get('분류', ''):14} {p}"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("q", nargs="?", default="")
    ap.add_argument("--cat")
    ap.add_argument("--role")
    ap.add_argument("--roles", action="store_true")
    ap.add_argument("--dirs", action="store_true")
    ap.add_argument("--play", action="store_true")
    ap.add_argument("-n", type=int, default=30)
    a = ap.parse_args()

    if a.dirs:
        for tag, root in config.SFX_ROOTS.items():
            n = sum(1 for p in root.rglob("*") if p.suffix.lower() in AUDIO) if root.exists() else 0
            print(f"{tag:4} {'있음' if root.exists() else '없음!'} {n:4}개  {root}")
        print(f"청음 {config.SFX_PREVIEW}")
        return
    if a.roles:
        for k, (f, mx, db, al, mean, use) in ROLES.items():
            print(f"{k:7} {mean:2} {f:34} 최대{mx}s {db:+d}dB {al:5}  {use}")
        return

    grade, ok, bad = index()
    fdb, dflt = file_db()
    hits = []
    if a.role:
        f = ROLES[a.role][0]
        hits = [(t, p) for t, p in walk() if p.name == f]
    elif a.cat:
        rs = [r for r in grade.values() if r.get("분류", "").startswith(a.cat)]
        rs.sort(key=lambda r: (ORDER.get(r["등급"], 9), -r.get("점수", 0)))
        hits = [("등급표", Path(r["파일"])) for r in rs[:a.n]]
    else:
        hits = [(t, p) for t, p in walk() if a.q.lower() in p.name.lower()][:a.n]
    if not hits:
        print("없음 — 다른 낱말로, 또는 --dirs 로 폴더가 있는지 확인")
        return
    for t, p in hits:
        print(row(t, p, grade, ok, bad, fdb, dflt))
    if a.play:
        os.startfile(str(hits[0][1]))


if __name__ == "__main__":
    main()

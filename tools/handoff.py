# -*- coding: utf-8 -*-
r"""두 컴퓨터 분업 — 기획(이 PC) ↔ 제작(새 PC). 건 폴더 하나로 주고받고, 파일마다 쓰는 쪽이 정해져 있다.

    python tools/handoff.py 역할                 # 이 컴퓨터가 기획인지 제작인지
    python tools/handoff.py 상태                 # 최신으로 받은 뒤 건마다 지금 단계와 «내가 할 일»
    python tools/handoff.py 새건 <건이름>         # (기획) 핸드오프/<날짜>_<건이름>/ 만들고 지시서 틀
    python tools/handoff.py 올리기 "<메시지>"     # 내 역할 파일만 커밋 → pull --rebase → push (남의 파일이 섞이면 거부)

건 폴더(핸드오프/<YYYY-MM-DD>_<건>/)와 쓰는 쪽
  00_지시서.md      기획   원문 경로(제작 PC 기준)·느낌·사장님 지시 원문·이번 건 단계(분석부터 / 바로 제작)
  10_분석/          제작   받아쓰기·자막 목록·화면 OCR 요약·화면 모음(jpg)·층 정보 — 기획이 연출을 짜는 재료
  20_연출표.md      기획   장면표(자막 글로 시각을 잡고, OCR 글자로 위치를 잡는다) — 제작이 그대로 만든다
  20_연출표.py      기획   (선택) tools/scenes 형식 연출표 코드
  30_결과.md        제작   만든 것·검수(넣을 때 1번·끝나고 1번) 결과·받은 피드백 원문·길라잡이 반영 요청
  20_쇼츠기획.md    기획   (쇼츠가 있는 건만) 쇼츠 기획 — 숏폼 세션이 그대로 만든다
  40_쇼츠결과.md    숏폼   쇼츠 납품·검수·받은 피드백 원문·반영 요청
그 밖에 쓰는 쪽
  기획: CLAUDE.md · .claude/ · templates/ · tones/ · 피드백/ · 기록/ · 핸드오프/*/00_*·20_*
  제작: tools/ · 핸드오프/*/10_분석/ · 핸드오프/*/30_* · 핸드오프/제작로그.md
  숏폼: 핸드오프/*/40_* · tools_shorts/ · 핸드오프/숏폼로그.md
숏폼(10-15): 제작 PC 의 두 번째 받은 폴더(D:\숏폼전용)에서만 연다. 그 폴더의 핸드오프/역할.local.json(git 제외)
  {"역할": "숏폼", "롱폼경로": "<롱폼 저장소 절대경로>"} 가 있으면 역할 «숏폼»이 먼저다. 롱폼 제작 세션은 쇼츠를 만들지 않는다.
(큰 파일 — 원문·렌더·납품 영상 — 은 git 에 넣지 않는다. 납품은 제작 PC 의 납품/ 에 생기고 사장님이 그 컴퓨터에서 본다.)
"""
import datetime
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HO = ROOT / "핸드오프"
ROLE_FILE = HO / "역할.json"
LOCAL_ROLE = HO / "역할.local.json"   # 숏폼 폴더에만(git 제외)

OWN = {
    "기획": ["CLAUDE.md", ".claude/", "templates/", "tones/", "피드백/", "기록/", "README.md", ".gitignore", "핸드오프/README.md",
           "핸드오프/역할.json", "핸드오프/*/00_", "핸드오프/*/20_"],
    "제작": ["tools/", "핸드오프/*/10_분석/", "핸드오프/*/30_", "핸드오프/제작로그.md", "소재/"],
    "숏폼": ["핸드오프/*/40_", "tools_shorts/", "핸드오프/숏폼로그.md"],
}


def sh(*a, check=True):
    r = subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode:
        print(r.stdout, r.stderr)
        raise SystemExit(f"git {' '.join(a)} 실패")
    return r.stdout


def local_role():
    """역할.local.json(숏폼 폴더) → dict, 없으면 None."""
    if not LOCAL_ROLE.exists():
        return None
    return json.load(open(LOCAL_ROLE, encoding="utf-8-sig"))


def role():
    import os
    me = os.environ.get("COMPUTERNAME", "")
    lr = local_role()
    if lr and lr.get("역할") == "숏폼":
        return "숏폼", me
    d = json.load(open(ROLE_FILE, encoding="utf-8"))
    return ("기획" if me == d["기획"] else "제작"), me


def owned(path, r):
    from fnmatch import fnmatch
    for p in OWN[r]:
        if "*" in p:
            if fnmatch(path, p + "*"):
                return True
        elif path == p or path.startswith(p):
            return True
    return False


def stage(job):
    """건 폴더 → (단계, 다음에 할 쪽)."""
    f = {p.name for p in job.iterdir()}
    ana = (job / "10_분석").exists() and any((job / "10_분석").iterdir())
    plan = "20_연출표.md" in f
    res = job / "30_결과.md"
    want_ana = "분석부터" in (job / "00_지시서.md").read_text(encoding="utf-8") if "00_지시서.md" in f else False
    if "00_지시서.md" not in f:
        return "지시서 없음", "기획"
    if res.exists():
        txt = res.read_text(encoding="utf-8")
        if "상태: 완료" in txt and (not plan or res.stat().st_mtime >= (job / "20_연출표.md").stat().st_mtime or "연출표 판:" in txt):
            fb = "받은 피드백" in txt and "(없음)" not in txt.split("받은 피드백", 1)[1][:80]
            return ("완료 · 피드백 있음 → 기획이 길라잡이 반영" if fb else "완료 — 사장님 확인 대기"), ("기획" if fb else "사장님")
    if want_ana and not ana:
        return "분석 대기", "제작"
    if not plan:
        return ("분석 완료 → 연출표 대기" if ana else "연출표 대기"), "기획"
    return "제작 대기", "제작"


def stage_shorts(job):
    """쇼츠 단계 → (단계, 다음에 할 쪽), 쇼츠 기획이 없는 건은 None."""
    if not (job / "20_쇼츠기획.md").exists():
        return None
    sr = job / "40_쇼츠결과.md"
    if sr.exists():
        txt = sr.read_text(encoding="utf-8")
        if "상태: 완료" in txt:
            fb = "받은 피드백" in txt and "(없음)" not in txt.split("받은 피드백", 1)[1][:80]
            return ("쇼츠 완료 · 피드백 → 기획", "기획") if fb else ("쇼츠 완료 — 사장님 확인 대기", "사장님")
    lr = job / "30_결과.md"
    if not (lr.exists() and "상태: 완료" in lr.read_text(encoding="utf-8")):
        return "쇼츠 — 롱폼 대기", "제작"
    return "숏폼 대기", "숏폼"


def cmd_status(pull=True):
    if pull:
        sh("pull", "--rebase", "--autostash", check=False)
    r, me = role()
    print(f"이 컴퓨터: {me} → 역할 «{r}»")
    jobs = sorted(p for p in HO.iterdir() if p.is_dir() and p.name[:2] == "20") if HO.exists() else []
    if not jobs:
        print("건 없음")
    if r == "숏폼":
        lr = local_role() or {}
        print(f"롱폼 저장소(읽기만): {lr.get('롱폼경로', '(역할.local.json 에 롱폼경로 없음)')}")
    for j in jobs:
        st, who = stage(j)
        mark = "  ← 내 차례" if who == r else ""
        print(f"- {j.name}: {st} (다음: {who}){mark}")
        ss = stage_shorts(j)
        if ss:
            mark = "  ← 내 차례" if ss[1] == r else ""
            print(f"    쇼츠: {ss[0]} (다음: {ss[1]}){mark}")


def cmd_new(name):
    r, _ = role()
    if r != "기획":
        raise SystemExit("새 건은 기획 컴퓨터에서 만든다")
    d = HO / f"{datetime.date.today():%Y-%m-%d}_{name}"
    d.mkdir(parents=True, exist_ok=True)
    t = d / "00_지시서.md"
    if not t.exists():
        t.write_text((HO / "_지시서_틀.md").read_text(encoding="utf-8").replace("<건>", name), encoding="utf-8")
    print(d)


def cmd_push(msg):
    r, me = role()
    sh("add", "-A")
    staged = [l for l in sh("diff", "--cached", "--name-only", "-z").split("\0") if l]
    bad = [s for s in staged if not owned(s, r)]
    if bad:
        sh("reset", "-q")
        print("★ 내 역할(" + r + ") 파일이 아닌 것이 섞여 있어 올리지 않았다:")
        for b in bad:
            print("   ", b)
        print("→ 남의 파일은 고치지 말고 30_결과.md(제작) / 00_지시서.md(기획)에 «반영 요청»으로 적는다.")
        raise SystemExit(1)
    if not staged:
        print("올릴 것 없음")
    else:
        sh("commit", "-q", "-m", f"[{r}] {msg}\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
    sh("pull", "--rebase", "-q")
    sh("push", "-q")
    print(f"올림({r}): {len(staged)}개 파일")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sh("config", "core.quotepath", "false", check=False)
    a = sys.argv[1:] or ["상태"]
    if a[0] == "역할":
        print(*role())
    elif a[0] == "상태":
        cmd_status(pull="--받기없이" not in a)
    elif a[0] == "새건":
        cmd_new(a[1])
    elif a[0] == "올리기":
        cmd_push(a[1] if len(a) > 1 else "핸드오프")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()

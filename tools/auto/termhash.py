# -*- coding: utf-8 -*-
r"""금지어(고객·업체 실명)를 git 에 실명 없이 넘기는 지문 — 기획이 만들고 제작이 대조한다.

    python tools/auto/termhash.py 만들기 <금지어.txt(비공개)> <핸드오프/<건>/00_금지어지문.json>
    from tools.auto.termhash import load, hit;  d = load(p);  hit("OCR 글자", d) → True/False

글자는 띄어쓰기·문장부호를 빼고 소문자로 맞춘 뒤, 금지어 길이마다 «솔트+글자»의 sha256 앞 16자.
OCR 글자는 같은 길이 조각을 모두 지문 내어 대조(포함 검사). 허용 줄(«허용: …»)은 지문 없이 그대로 넘긴다(번호 앞자리 등 실명 아님).
"""
import hashlib
import json
import re
import secrets
import sys

NORM = re.compile(r"[\s.,·\-_:;'\"()\[\]{}]")


def norm(s):
    return NORM.sub("", s).lower()


def h(salt, s):
    return hashlib.sha256((salt + s).encode("utf-8")).hexdigest()[:16]


def make(src, dst):
    lines = [l.strip() for l in open(src, encoding="utf-8") if l.strip() and not l.startswith("#")]
    allow = [l[3:].strip() for l in lines if l.startswith("허용:")]
    terms = [norm(l) for l in lines if not l.startswith("허용:")]
    salt = secrets.token_hex(8)
    by = {}
    for t in terms:
        if len(t) >= 2:
            by.setdefault(str(len(t)), []).append(h(salt, t))
    json.dump({"_설명": "금지어 지문(실명 아님) — tools/auto/termhash.py", "salt": salt, "by_len": by, "allow": allow},
              open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"금지어 {len(terms)}개 → {dst}")


def load(p):
    return json.load(open(p, encoding="utf-8"))


def hit(text, d):
    s = norm(text)
    for L, hs in d["by_len"].items():
        n = int(L); hs = set(hs)
        for i in range(0, max(0, len(s) - n) + 1):
            if h(d["salt"], s[i:i + n]) in hs:
                return True
    return False


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "만들기":
        make(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)

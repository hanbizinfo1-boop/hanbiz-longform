# -*- coding: utf-8 -*-
"""성제관01 쇼츠 소리 다시 섞기(숏폼 세션 10-15) — 숏폼에서 다시 렌더한 장면의 효과음 계기(EVENTS)가 롱폼 판과 달라졌을 때만.

    py -3.11 tools_shorts/sjk01_remix.py S3 [S…]

롱폼 `tools/scenes/sjk01/shorts_assemble.audio()` 를 그대로 쓰되(효과음 고르기·sfx_bus·BGM·−14 LUFS 같은 규칙),
읽고 쓰는 곳만 이 폴더로 돌린다 — 계기 = `_tmp/sjk01/render/sh_SN_events.json`(숏폼 렌더),
목소리 = 롱폼 `_tmp/sjk01/shorts/SN_목소리.wav` 를 이 폴더로 복사, 결과 = `_tmp/sjk01/shorts/SN_소리.wav`.
롱폼 저장소에는 아무것도 쓰지 않는다. `sjk01_resub.py` 는 이 폴더 소리가 있으면 그걸 먼저 쓴다.
"""
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
LONG = Path(json.loads((HERE / "핸드오프/역할.local.json").read_text(encoding="utf-8"))["롱폼경로"])
sys.path.insert(0, str(LONG))
import tools.scenes.sjk01.shorts_assemble as SA  # noqa: E402  (롱폼 도구 — 읽기만)

assert Path(SA.__file__).resolve().is_relative_to(LONG), SA.__file__


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    SA.ROOT = HERE                                   # 계기 파일을 이 폴더 렌더에서 읽게
    SA.SHORTS_DIR = HERE / "_tmp/sjk01/shorts"       # 쓰는 곳도 이 폴더
    SA.SHORTS_DIR.mkdir(parents=True, exist_ok=True)
    for name in sys.argv[1:]:
        shutil.copy2(LONG / f"_tmp/sjk01/shorts/{name}_목소리.wav", SA.SHORTS_DIR / f"{name}_목소리.wav")
        sc = json.loads((LONG / f"tools/scenes/sjk01/data/sh_{name}.js").read_text(encoding="utf-8").split("=", 1)[1].strip().rstrip(";"))
        placed, dropped = SA.audio(name, sc, SA.SHORTS_DIR / f"{name}_소리.wav")
        json.dump({"sfx": placed, "dropped": dropped}, open(SA.SHORTS_DIR / f"{name}_조립보고.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(name, "→", SA.SHORTS_DIR / f"{name}_소리.wav", f"효과음 {len(placed)} · 뺌 {len(dropped)}")


if __name__ == "__main__":
    main()

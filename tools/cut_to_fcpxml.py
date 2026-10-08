"""컷 계획을 Final Cut Pro 7 XML(xmeml) 로 내보낸다 — 프리미어가 임포트하는 교환 포맷.

렌더된 파일 대신 **타임라인**을 넘기기 위해서다. 프리미어에서 열면 컷이 이미 나뉜
상태로 뜨고, 원본 4K 파일을 그대로 참조하므로 화질 손실이 없다. 컷 지점이 마음에
안 들면 그 자리에서 밀면 된다 — 렌더본은 그게 안 된다.

표준 라이브러리만 쓴다. 새 패키지를 깔지 않는다.

주의:
  · 프레임 번호는 `round(초 * fps)` 로 만든다. fps 는 소재에서 읽은 실측값(60000/1001).
  · 경로에 한글이 있으므로 pathurl 은 URL 인코딩한다.
  · 비디오·오디오 clipitem 을 `link` 로 묶어 프리미어에서 함께 움직이게 한다.
"""

import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape


def probe(video: Path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate",
         "-show_entries", "format=duration",
         "-of", "json", str(video)],
        capture_output=True, text=True, check=True,
    ).stdout
    j = json.loads(out)
    s = j["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    return int(s["width"]), int(s["height"]), float(num) / float(den), float(j["format"]["duration"])


def path_to_url(p: Path) -> str:
    """Windows 경로를 프리미어가 읽는 file URL 로. 한글은 퍼센트 인코딩한다."""
    s = str(p).replace("\\", "/")
    if len(s) > 1 and s[1] == ":":          # C:/... → /C:/...
        s = "/" + s
    return "file://localhost" + quote(s, safe="/:")


def rate_xml(timebase: int, ntsc: bool, indent: str) -> str:
    return (f"{indent}<rate>\n"
            f"{indent}  <timebase>{timebase}</timebase>\n"
            f"{indent}  <ntsc>{'TRUE' if ntsc else 'FALSE'}</ntsc>\n"
            f"{indent}</rate>\n")


def main():
    plan_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    p = json.loads(plan_path.read_text(encoding="utf-8"))
    src = Path(p["source"])
    keep = p["keep"]

    width, height, fps, duration = probe(src)

    # 59.94 → timebase 60 + ntsc TRUE. 29.97 → 30 + TRUE. 정수 fps 면 ntsc FALSE.
    timebase = int(round(fps))
    ntsc = abs(fps - timebase) > 0.001

    def f(t: float) -> int:
        return int(round(t * fps))

    src_total_frames = f(duration)
    seq_name = out_path.stem
    file_url = path_to_url(src)
    file_name = escape(src.name)

    video_items, audio_items = [], []
    timeline = 0
    for idx, (s, e) in enumerate(keep, start=1):
        sin, sout = f(s), f(e)
        length = sout - sin
        if length <= 0:
            continue
        tstart, tend = timeline, timeline + length
        timeline = tend

        # 파일 정의는 첫 clipitem 에만 싣고, 이후는 id 로만 참조한다 (xmeml 규약)
        if idx == 1:
            file_el = (
                f'          <file id="file-1">\n'
                f'            <name>{file_name}</name>\n'
                f'            <pathurl>{file_url}</pathurl>\n'
                + rate_xml(timebase, ntsc, "            ")
                + f'            <duration>{src_total_frames}</duration>\n'
                f'            <media>\n'
                f'              <video>\n'
                f'                <samplecharacteristics>\n'
                f'                  <width>{width}</width>\n'
                f'                  <height>{height}</height>\n'
                f'                </samplecharacteristics>\n'
                f'              </video>\n'
                f'              <audio>\n'
                f'                <channelcount>2</channelcount>\n'
                f'              </audio>\n'
                f'            </media>\n'
                f'          </file>\n'
            )
        else:
            file_el = '          <file id="file-1"/>\n'

        link = (
            f'            <link><linkclipref>v{idx}</linkclipref></link>\n'
            f'            <link><linkclipref>a{idx}</linkclipref></link>\n'
        )

        video_items.append(
            f'        <clipitem id="v{idx}">\n'
            f'          <name>{file_name}</name>\n'
            f'          <enabled>TRUE</enabled>\n'
            f'          <duration>{src_total_frames}</duration>\n'
            + rate_xml(timebase, ntsc, "          ")
            + f'          <start>{tstart}</start>\n'
            f'          <end>{tend}</end>\n'
            f'          <in>{sin}</in>\n'
            f'          <out>{sout}</out>\n'
            + file_el
            + f'          <sourcetrack>\n'
            f'            <mediatype>video</mediatype>\n'
            f'            <trackindex>1</trackindex>\n'
            f'          </sourcetrack>\n'
            + link.replace("            ", "          ")
            + f'        </clipitem>\n'
        )

        audio_items.append(
            f'        <clipitem id="a{idx}">\n'
            f'          <name>{file_name}</name>\n'
            f'          <enabled>TRUE</enabled>\n'
            f'          <duration>{src_total_frames}</duration>\n'
            + rate_xml(timebase, ntsc, "          ")
            + f'          <start>{tstart}</start>\n'
            f'          <end>{tend}</end>\n'
            f'          <in>{sin}</in>\n'
            f'          <out>{sout}</out>\n'
            f'          <file id="file-1"/>\n'
            f'          <sourcetrack>\n'
            f'            <mediatype>audio</mediatype>\n'
            f'            <trackindex>1</trackindex>\n'
            f'          </sourcetrack>\n'
            + link.replace("            ", "          ")
            + f'        </clipitem>\n'
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE xmeml>\n'
        '<xmeml version="4">\n'
        '  <sequence id="sequence-1">\n'
        f'    <name>{escape(seq_name)}</name>\n'
        f'    <duration>{timeline}</duration>\n'
        + rate_xml(timebase, ntsc, "    ")
        + '    <timecode>\n'
        + rate_xml(timebase, ntsc, "      ")
        + '      <string>00:00:00:00</string>\n'
        '      <frame>0</frame>\n'
        '      <displayformat>NDF</displayformat>\n'
        '    </timecode>\n'
        '    <media>\n'
        '      <video>\n'
        '        <format>\n'
        '          <samplecharacteristics>\n'
        + rate_xml(timebase, ntsc, "            ")
        + f'            <width>{width}</width>\n'
        f'            <height>{height}</height>\n'
        '            <pixelaspectratio>square</pixelaspectratio>\n'
        '          </samplecharacteristics>\n'
        '        </format>\n'
        '        <track>\n'
        + "".join(video_items)
        + '        </track>\n'
        '      </video>\n'
        '      <audio>\n'
        '        <track>\n'
        + "".join(audio_items)
        + '        </track>\n'
        '      </audio>\n'
        '    </media>\n'
        '  </sequence>\n'
        '</xmeml>\n'
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(xml, encoding="utf-8")

    print(f"컷 {len(keep)}개 → clipitem {len(video_items)}쌍")
    print(f"시퀀스 길이: {timeline} 프레임 ({timeline/fps:.1f}초 = {timeline/fps/60:.2f}분)")
    print(f"규격: {width}x{height} / timebase {timebase} ntsc={'TRUE' if ntsc else 'FALSE'}")
    print(f"저장: {out_path}  ({out_path.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()

"""컷 계획을 «녹화 + 카메라» 두 층 FCP7 XML(xmeml) 로 내보낸다.

사장님 강의 편집의 뼈대(8강 실측, `강사님-강의편집/편집분석-8강.md`)를 그대로 만든다.

    V1  화면녹화 (1080p30)          — 카메라와 같은 자리에서 같이 잘린다
    V2  카메라 4K → 비율 50%         — 1920×1080 시퀀스를 꽉 채운다
    A1  카메라 소리(말)              — 녹화 소리는 올리지 않는다
    시퀀스 1920×1080 / 59.94

컷 계획(`cut_plan.json`)은 카메라 시각 기준이다. 녹화 시각 = 카메라 시각 − offset.
offset 은 두 소리의 상호상관으로 실측해서 넣는다 (16: 5.594초, 17: 1.781초).
녹화가 시작되기 전·끝난 뒤 구간은 V1 을 비워 둔다.

    python cut_to_fcpxml_dual.py <cut_plan.json> <녹화.mp4> <offset초> <출력.xml> [pip.json]

pip.json (선택) = [[시작, 끝], …] 카메라 원본 시각. 이 구간은 «녹화 전체화면 + 카메라 PIP»:
  카메라를 **V3 에 따로** 올린다(V2 는 그 구간 비움). 비율 19% · 좌하단(8강 실측: 위치 0.0927, 0.9259) · **라벨 색(Cerulean)**.
  원형 마스크(불투명도 › Mask2)는 XML 로 못 넘긴다 → 프리미어에서 라벨로 PIP 클립을 골라
  8강 PIP 클립의 속성(모션 + 불투명도)을 «속성 붙여넣기» 하면 8강과 똑같아진다.
  PIP 경계가 클립 가운데 오면 그 자리에서 클립을 나눈다 (같은 원본이 이어지므로 화면은 튀지 않는다).

`cut_to_fcpxml.py`(카메라 한 층)에서 갈라져 나왔다. 그쪽 XML 은 프리미어 임포트가 확인됐다
(강사님.prproj «13~15강_컷편집»). 표준 라이브러리만 쓴다.
"""

import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape

SEQ_W, SEQ_H = 1920, 1080
SEQ_FPS = 60000 / 1001
CAM_SCALE = 50          # 4K → 1080 (8강 실측값)
PIP_SCALE = 19          # 8강 PIP 실측
PIP_POS = (0.0927083, 0.9259260)   # 시퀀스 기준 0~1 (8강 실측) → FCP center 는 중심 기준 비율로 바꿔 넣는다


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
    s = str(p).replace("\\", "/")
    if len(s) > 1 and s[1] == ":":
        s = "/" + s
    return "file://localhost" + quote(s, safe="/:")


def rate_xml(fps: float, ind: str) -> str:
    tb = int(round(fps))
    ntsc = abs(fps - tb) > 0.001
    return (f"{ind}<rate>\n{ind}  <timebase>{tb}</timebase>\n"
            f"{ind}  <ntsc>{'TRUE' if ntsc else 'FALSE'}</ntsc>\n{ind}</rate>\n")


def file_xml(fid, src: Path, w, h, fps, dur, audio: bool, first: bool) -> str:
    if not first:
        return f'          <file id="{fid}"/>\n'
    aud = ('              <audio>\n                <channelcount>2</channelcount>\n'
           '              </audio>\n') if audio else ""
    return (f'          <file id="{fid}">\n'
            f'            <name>{escape(src.name)}</name>\n'
            f'            <pathurl>{path_to_url(src)}</pathurl>\n'
            + rate_xml(fps, "            ")
            + f'            <duration>{int(round(dur * fps))}</duration>\n'
            f'            <media>\n              <video>\n                <samplecharacteristics>\n'
            f'                  <width>{w}</width>\n                  <height>{h}</height>\n'
            f'                </samplecharacteristics>\n              </video>\n{aud}'
            f'            </media>\n          </file>\n')


def scale_filter(scale: int, center=None) -> str:
    cen = ""
    if center:
        cen = ('              <parameter>\n                <parameterid>center</parameterid>\n'
               '                <name>Center</name>\n'
               f'                <value><horiz>{center[0]:.5f}</horiz><vert>{center[1]:.5f}</vert></value>\n'
               '              </parameter>\n')
    return ('          <filter>\n            <effect>\n'
            '              <name>Basic Motion</name>\n              <effectid>basic</effectid>\n'
            '              <effectcategory>motion</effectcategory>\n'
            '              <effecttype>motion</effecttype>\n              <mediatype>video</mediatype>\n'
            '              <parameter>\n                <parameterid>scale</parameterid>\n'
            '                <name>Scale</name>\n                <valuemin>0</valuemin>\n'
            f'                <valuemax>1000</valuemax>\n                <value>{scale}</value>\n'
            '              </parameter>\n' + cen + '            </effect>\n          </filter>\n')


def clip(cid, name, tstart, tend, sin, sout, dur_frames, file_el, mtype, links, extra=""):
    ln = "".join(f'          <link><linkclipref>{l}</linkclipref></link>\n' for l in links)
    return (f'        <clipitem id="{cid}">\n'
            f'          <name>{escape(name)}</name>\n          <enabled>TRUE</enabled>\n'
            f'          <duration>{dur_frames}</duration>\n'
            + rate_xml(SEQ_FPS, "          ")
            + f'          <start>{tstart}</start>\n          <end>{tend}</end>\n'
            f'          <in>{sin}</in>\n          <out>{sout}</out>\n'
            + file_el + extra
            + f'          <sourcetrack>\n            <mediatype>{mtype}</mediatype>\n'
            f'            <trackindex>1</trackindex>\n          </sourcetrack>\n'
            + ln + '        </clipitem>\n')


def main():
    plan_path, rec, out_path = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[4])
    # offset 자리에 json 을 주면 [[카메라 초, offset], …] 곡선 — 녹화 시계가 카메라와 조금씩 어긋날 때(빡이사DB 10-01).
    # 클립마다 그 클립 시작 시각의 offset 을 쓴다(클립 하나 안의 어긋남은 1프레임 미만).
    if sys.argv[3].endswith(".json"):
        curve = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
        cx, cy = [c[0] for c in curve], [c[1] for c in curve]

        def offset_at(t):
            if t <= cx[0]:
                return cy[0]
            for (x0, y0), (x1, y1) in zip(curve, curve[1:]):
                if t <= x1:
                    return y0 + (y1 - y0) * (t - x0) / (x1 - x0)
            return cy[-1]
        offset = cy[0]
    else:
        offset = float(sys.argv[3])

        def offset_at(t):
            return offset
    p = json.loads(plan_path.read_text(encoding="utf-8"))
    cam = Path(p["source"])
    pips = json.loads(Path(sys.argv[5]).read_text(encoding="utf-8")) if len(sys.argv) > 5 else []

    # 컷 구간을 PIP 경계에서 나눈다 → (시작, 끝, PIP 여부)
    keep = []
    for s, e in p["keep"]:
        cuts = sorted({x for a, b in pips for x in (a, b) if s < x < e})
        edges = [s] + cuts + [e]
        for a, b in zip(edges, edges[1:]):
            mid = (a + b) / 2
            keep.append((a, b, any(x <= mid < y for x, y in pips)))

    cw, ch, cfps, cdur = probe(cam)
    rw, rh, rfps, rdur = probe(rec)

    def f(t):                   # 초 → 시퀀스 프레임 (in/out 도 시퀀스 단위로 쓴다)
        return int(round(t * SEQ_FPS))

    cam_len, rec_len = f(cdur), f(rdur)
    v1, v2, v3, a1 = [], [], [], []   # v3 = PIP(마스크 씌울) 카메라만
    timeline = 0
    rec_first = cam_first = True
    pip_frames = 0
    for i, (s, e, pip) in enumerate(keep, start=1):
        sin, sout = f(s), f(e)
        n = sout - sin
        if n <= 0:
            continue
        t0, t1 = timeline, timeline + n
        timeline = t1

        # 녹화: 카메라 시각 − offset. 녹화가 없는 앞·뒤는 잘라 낸다
        off = offset_at(s)
        off_f = f(off)
        rs, re_ = s - off, e - off
        has_rec = re_ > 0 and rs < rdur
        vid = f"v3-{i}" if pip else f"v2-{i}"
        links = [vid, f"a1-{i}"] + ([f"v1-{i}"] if has_rec else [])

        if pip:
            pip_frames += n
            # 위치(center)를 넣었더니 프리미어에서 화면 밖으로 나갔다(09-23 사장님 확인) → 전체화면 그대로 두고
            # 사장님이 8강 PIP 속성(모션+불투명도 마스크)을 붙여 넣으면 좌하단 원형이 된다
            motion = (scale_filter(CAM_SCALE)
                      + '          <labels><label2>Cerulean</label2></labels>\n')
        else:
            motion = scale_filter(CAM_SCALE)
        # PIP 은 V3 로 따로 올린다 — 그 트랙만 통째로 골라 마스크를 씌울 수 있게 (사장님 요청 09-23)
        (v3 if pip else v2).append(clip(vid, cam.name + (" PIP" if pip else ""), t0, t1, sin, sout, cam_len,
                                        file_xml("file-cam", cam, cw, ch, cfps, cdur, True, cam_first),
                                        "video", links, motion))
        a1.append(clip(f"a1-{i}", cam.name, t0, t1, sin, sout, cam_len,
                       '          <file id="file-cam"/>\n', "audio", links))
        cam_first = False

        if has_rec:
            lead = max(0.0, -rs)                    # 녹화 시작 전 부분
            tail = max(0.0, re_ - rdur)             # 녹화 끝난 뒤 부분
            rt0, rt1 = t0 + f(lead), t1 - f(tail)
            # 녹화 in 을 따로 반올림하면 클립마다 싱크가 1프레임씩 흔들린다 → 카메라 in 에서 정수 오프셋을 뺀다
            ri = sin + (rt0 - t0) - off_f
            ro = ri + (rt1 - rt0)
            if rt1 > rt0:
                v1.append(clip(f"v1-{i}", rec.name, rt0, rt1, ri, ro, rec_len,
                               file_xml("file-rec", rec, rw, rh, rfps, rdur, False, rec_first),
                               "video", links))
                rec_first = False

    def track(items):
        return '        <track>\n' + "".join(items) + '        </track>\n'

    # 버벅임을 뺀 자리 (apply_removals.py 가 넣는다) → 시퀀스 마커
    markers = ""
    for m in p.get("markers", []):
        name = escape("%02d %s" % (m["no"], m["label"]))
        markers += ('    <marker>\n'
                    f'      <name>{name}</name>\n'
                    f'      <comment>{escape(m["text"])}</comment>\n'
                    f'      <in>{f(m["t"])}</in>\n      <out>-1</out>\n'
                    '    </marker>\n')

    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="4">\n'
           '  <sequence id="sequence-1">\n'
           f'    <name>{escape(out_path.stem)}</name>\n    <duration>{timeline}</duration>\n'
           + rate_xml(SEQ_FPS, "    ")
           + '    <timecode>\n' + rate_xml(SEQ_FPS, "      ")
           + '      <string>00:00:00:00</string>\n      <frame>0</frame>\n'
           '      <displayformat>NDF</displayformat>\n    </timecode>\n'
           + markers
           + '    <media>\n      <video>\n        <format>\n          <samplecharacteristics>\n'
           + rate_xml(SEQ_FPS, "            ")
           + f'            <width>{SEQ_W}</width>\n            <height>{SEQ_H}</height>\n'
           '            <pixelaspectratio>square</pixelaspectratio>\n'
           '          </samplecharacteristics>\n        </format>\n'
           + track(v1).replace('        <track>', '        <track>', 1)
           + track(v2)
           + (track(v3) if v3 else "")
           + '      </video>\n      <audio>\n'
           + track(a1)
           + '      </audio>\n    </media>\n  </sequence>\n</xmeml>\n')

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(xml, encoding="utf-8")
    print(f"카메라 {cam.name} {cw}x{ch} {cfps:.3f}fps · 녹화 {rec.name} {rw}x{rh} {rfps:.3f}fps")
    print(f"offset {offset:+.3f}초 · 컷 구간 {len(keep)}개 → V1 {len(v1)} / V2 {len(v2)} / A1 {len(a1)}")
    if pips:
        print(f"PIP(녹화 화면) {pip_frames / SEQ_FPS:.1f}초 = {pip_frames / max(timeline, 1) * 100:.1f}% · 나머지 인물 전체화면")
    print(f"시퀀스 {timeline}프레임 = {timeline / SEQ_FPS:.2f}초 ({SEQ_W}x{SEQ_H} 59.94)")
    print(f"저장: {out_path}  ({out_path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()

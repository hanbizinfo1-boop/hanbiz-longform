# -*- coding: utf-8 -*-
r"""강의 자료 «얹을 것만» XML — 영상은 V3, 효과음은 A2부터 (사장님 09-30 «다음부터 영상은 V3 음성은 A2»).

XML을 프리미어로 불러오면 트랙 번호가 그대로 살아 있어서, 복사해 강의 시퀀스에 붙일 때 V3·A2 자리에 바로 앉는다.
V1·V2·A1은 빈 트랙으로 깔아 자리만 잡는다. 효과음이 겹치면 A3, A4…로 넘친다.

    import lec_xml
    lec_xml.write(out_xml, seq_name, mov, dur_s, t0_s, sfx=[(시각초, wav경로), …], fps=59.94)
"""
import subprocess
from pathlib import Path

V_TRACK, A_TRACK = 3, 2


def url(p):
    return "file://localhost/" + str(p).replace("\\", "/")


def rate_of(fps):
    """(timebase, ntsc, 프레임 변환 함수)."""
    if abs(fps - 59.94) < 0.01:
        return 60, lambda t: int(round(t * 60000 / 1001))
    if abs(fps - 29.97) < 0.01:
        return 30, lambda t: int(round(t * 30000 / 1001))
    raise ValueError(f"시퀀스 fps {fps} 는 아직 안 다룬다")


def write(out_xml, seq_name, mov, dur_s, t0_s, sfx, fps, tag="c"):
    tb, fr = rate_of(fps)
    RATE = f"<rate><timebase>{tb}</timebase><ntsc>TRUE</ntsc></rate>"
    mov = Path(mov)
    n_mov = fr(dur_s)
    s0 = fr(t0_s)
    vclip = (f'<clipitem id="v-{tag}"><name>{mov.name}</name><enabled>TRUE</enabled>{RATE}<start>{s0}</start><end>{s0 + n_mov}</end>'
             f'<in>0</in><out>{n_mov}</out><file id="f-{tag}"><name>{mov.name}</name><pathurl>{url(mov)}</pathurl>{RATE}<duration>{n_mov}</duration>'
             '<media><video><samplecharacteristics><width>1920</width><height>1080</height></samplecharacteristics></video></media></file></clipitem>')
    items = []
    for k, (t, f) in enumerate(sorted(sfx, key=lambda x: x[0])):
        f = Path(f)
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                   capture_output=True, text=True).stdout)
        n = max(1, fr(dur))
        st = fr(t)
        items.append((t, t + dur, f'<clipitem id="a-{tag}-{k}"><name>{f.name}</name><enabled>TRUE</enabled>{RATE}<start>{st}</start><end>{st + n}</end><in>0</in><out>{n}</out>'
                                  f'<file id="fa-{tag}-{k}"><name>{f.name}</name><pathurl>{url(f)}</pathurl>{RATE}<duration>{n}</duration><media><audio><channelcount>2</channelcount></audio></media></file>'
                                  '<sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack></clipitem>'))
    tracks, ends = [], []                     # 겹치면 다음 트랙으로
    for t, e, it in items:
        for i, last in enumerate(ends):
            if last <= t:
                tracks[i].append(it)
                ends[i] = e
                break
        else:
            tracks.append([it])
            ends.append(e)
    empty = "<track><enabled>TRUE</enabled></track>"
    video = empty * (V_TRACK - 1) + f"<track>{vclip}<enabled>TRUE</enabled></track>"
    audio = empty * (A_TRACK - 1) + "".join(f"<track>{''.join(t)}<enabled>TRUE</enabled></track>" for t in tracks)
    end = s0 + n_mov + 2 * tb
    x = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="4"><sequence id="seq-' + tag + f'"><name>{seq_name}</name>'
         f"<duration>{end}</duration>{RATE}<media><video><format><samplecharacteristics>{RATE}<width>1920</width><height>1080</height>"
         f"<pixelaspectratio>square</pixelaspectratio></samplecharacteristics></format>{video}</video>"
         f"<audio>{audio}</audio></media></sequence></xmeml>\n")
    out_xml = Path(out_xml)
    out_xml.write_text(x, encoding="utf-8", newline="\n")
    return out_xml, [f"A{A_TRACK + i}" for i in range(len(tracks))]

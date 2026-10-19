"""Render a 120-second narrated screenshot walkthrough; not a live interaction recording.

Requires macOS say and imageio-ffmpeg (optional authoring dependency).
"""
import json
import subprocess
from pathlib import Path
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / '.runtime/demo'
TMP.mkdir(parents=True, exist_ok=True)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
chapters = json.loads((ROOT / 'docs/demo/narration.json').read_text())
for i, chapter in enumerate(chapters):
    speech = TMP / f'{i}.txt'
    speech.write_text(chapter['text'])
    subprocess.run(['say', '-r', '225', '-f', str(speech), '-o', str(TMP / f'{i}.aiff')], check=True)
    # Slowly pan across genuine full-page screenshots, preserving readable width.
    subprocess.run([FFMPEG, '-y', '-loop', '1', '-framerate', '12',
        '-i', str(ROOT / f"docs/screenshots/{chapter['screen']}.png"),
        '-i', str(TMP / f'{i}.aiff'),
        '-vf', "scale=1280:-2,pad=1280:max(720\\,ih):0:0:color=0x0b1016,crop=1280:720:0:'(ih-720)*min(t/29,1)',setsar=1",
        '-af', 'apad', '-t', '30', '-c:v', 'libx264', '-preset', 'fast', '-crf', '24',
        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '96k', str(TMP / f'{i}.mp4')], check=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
(TMP / 'concat.txt').write_text(''.join(f"file '{i}.mp4'\n" for i in range(4)))
subprocess.run([FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', str(TMP / 'concat.txt'),
    '-c', 'copy', '-movflags', '+faststart', str(ROOT / 'docs/demo/atlas-walkthrough.mp4')], check=True)
print('Created 120-second narrated screenshot walkthrough.')

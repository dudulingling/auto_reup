import subprocess
text = "@Zhiu'Nika:test"

# If we escape colon:
escaped = text.replace("'", "'\\''").replace(":", "\\:")
cmd = [
    'docker', 'exec', 'autoreup_celery_worker', 'ffmpeg', '-f', 'lavfi', '-i', 'color=c=black:s=64x64:d=1',
    '-vf', f"drawtext=text='{escaped}':fontcolor=white",
    '-y', '/tmp/out.mp4'
]
p = subprocess.run(cmd, capture_output=True, text=True)
print("SUCCESS" if "Error" not in p.stderr else "ERROR: " + p.stderr[-500:])
